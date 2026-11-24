// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity ^0.8.24;

// SKETCH ONLY. Compiles with solc 0.8.24 + OpenZeppelin 5.0.2. Tested locally (test/), not audited, not deployed.
// Spec: ../../spec/bill-to.md (requirement IDs F1..F12 noted inline).
// Built on OpenZeppelin Contracts v5.x.

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {EIP712} from "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {MessageHashUtils} from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import {SignatureChecker} from "@openzeppelin/contracts/utils/cryptography/SignatureChecker.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {Ownable, Ownable2Step} from "@openzeppelin/contracts/access/Ownable2Step.sol";

/// @title BillTo: an order bill minted as an NFT to whoever should pay it.
/// @notice One shared contract per chain. Merchants sign terms off chain (EIP-712),
///         the buyer submits them, the Bill NFT goes to the payer (or waits for a
///         claim link). The merchant offers up to four coins; the first payer picks one.
///         Full funding either pays the merchant at once or, in escrow mode, holds the
///         money until buyer and merchant both release it or the arbiter rules.
contract BillTo is ERC721, EIP712, ReentrancyGuard, Ownable2Step {
    using SafeERC20 for IERC20;

    // Open: waiting for money. Held: fully funded, in escrow. Expired is computed (Open && now >= expiry).
    enum Status { Open, Held, Paid, Cancelled, Refunded }

    /// One coin the merchant accepts and its price in that coin. token == address(0) means native ETH.
    struct Offer {
        address token;
        uint256 amount;
    }

    /// Terms the merchant signs.
    struct Terms {
        address merchant;          // receives funds; EOA or ERC-1271 contract (e.g. a co-op Safe)
        address buyer;             // may cancel with the merchant; releases escrow with the merchant
        address arbiter;           // escrow mode only: independent party who rules on a dispute (core.md E2, E3)
        Offer[] offers;            // 1 to MAX_OFFERS coins the merchant accepts (F11)
        uint64  expiry;            // unix seconds
        bytes32 orderHash;         // keccak256 of the merchant's order JSON (N5)
        bool    splitAllowed;
        uint16  minContributionBps; // share of the bill, in basis points, each split payment must reach; ignored if !splitAllowed
        bool    escrow;            // false: pay merchant at once on full funding. true: hold until released (5.2)
        uint32  escrowTimeout;     // escrow only: seconds a held bill waits before payers may take their money back; 0 = DEFAULT_ESCROW_TIMEOUT
        uint256 nonce;             // merchant chosen, one use
    }

    struct Bill {
        address merchant;
        address buyer;
        address arbiter;
        address token;             // set when the first payment picks a coin
        uint64  expiry;
        uint64  heldUntil;         // escrow: after this time an unreleased held bill refunds the payers
        uint32  escrowTimeout;
        Status  status;
        bool    splitAllowed;
        bool    escrow;
        bool    tokenChosen;
        bool    buyerReleased;
        bool    merchantReleased;
        uint16  minContributionBps;
        uint256 amount;            // set with token
        uint256 funded;
        bytes32 orderHash;
        address claimSigner;       // throwaway key from the claim link, or zero
    }

    uint256 public constant MAX_OFFERS = 4;
    uint32 public constant DEFAULT_ESCROW_TIMEOUT = 30 days; // Kenny 2026-11-23: adjustable per bill, 30 day default

    bytes32 private constant OFFER_TYPEHASH = keccak256("Offer(address token,uint256 amount)");
    bytes32 private constant TERMS_TYPEHASH = keccak256(
        "Terms(address merchant,address buyer,address arbiter,Offer[] offers,uint64 expiry,bytes32 orderHash,bool splitAllowed,uint16 minContributionBps,bool escrow,uint32 escrowTimeout,uint256 nonce)Offer(address token,uint256 amount)"
    );

    mapping(address => bool) public tokenAllowed;                         // F11
    mapping(bytes32 => bool) public termsUsed;                            // replay guard
    mapping(uint256 => Bill) public bills;
    mapping(uint256 => mapping(address => uint256)) public offerAmount;  // billId => token => price; 0 = not offered
    mapping(uint256 => mapping(address => uint256)) public contributed;  // F5
    uint256 public nextBillId = 1;

    event BillCreated(uint256 indexed billId, address indexed merchant, address indexed payer, bytes32 orderHash, bool escrow, uint64 expiry);
    event BillOffer(uint256 indexed billId, address indexed token, uint256 amount);
    event BillCoinPicked(uint256 indexed billId, address indexed token, uint256 amount);
    event BillHeld(uint256 indexed billId, uint256 amount);
    event BillReleaseApproved(uint256 indexed billId, address indexed by);
    event BillRuled(uint256 indexed billId, bool toMerchant);
    event BillClaimed(uint256 indexed billId, address indexed payer);
    event BillContribution(uint256 indexed billId, address indexed from, uint256 amount, uint256 funded);
    event BillPaid(uint256 indexed billId, address indexed merchant, uint256 amount);
    event BillCancelled(uint256 indexed billId, address indexed by);
    event BillRefunded(uint256 indexed billId);
    event Withdrawn(uint256 indexed billId, address indexed to, uint256 amount);
    event TokenAllowed(address indexed token, bool allowed);

    error BadSignature();
    error TermsReused();
    error TokenNotAllowed();
    error NotOpen();
    error Expired();
    error NotExpiredOrClosed();
    error BadAmount();
    error NotAllowed();
    error NothingToWithdraw();
    error Locked();
    error BadOffers();
    error WrongCoin();
    error BadArbiter();

    constructor(address admin)
        ERC721("Bill To", "BILL")
        EIP712("BillTo", "1")
        Ownable(admin) // N1: admin should be a multisig behind a timelock; it can only edit the token allowlist
    {}

    // ------------------------------------------------------------------ admin

    function setToken(address token, bool allowed) external onlyOwner {
        tokenAllowed[token] = allowed;
        emit TokenAllowed(token, allowed);
    }

    // ------------------------------------------------------------------ create (F1, F2)

    /// @param payer Wallet that receives the Bill NFT, or address(0) to hold it for a claim link.
    /// @param claimSigner Address of the throwaway claim key when payer == address(0).
    function createBill(Terms calldata t, bytes calldata merchantSig, address payer, address claimSigner)
        external
        returns (uint256 billId)
    {
        if (t.expiry <= block.timestamp) revert BadAmount();
        if (t.minContributionBps > 10_000) revert BadAmount();
        if (payer == address(0) && claimSigner == address(0)) revert NotAllowed();
        if (t.offers.length == 0 || t.offers.length > MAX_OFFERS) revert BadOffers();
        if (t.escrow && (t.arbiter == address(0) || t.arbiter == t.merchant || t.arbiter == t.buyer)) revert BadArbiter();

        bytes32 digest = termsDigest(t);
        if (termsUsed[digest]) revert TermsReused();
        if (!SignatureChecker.isValidSignatureNow(t.merchant, digest, merchantSig)) revert BadSignature();
        termsUsed[digest] = true;

        billId = nextBillId++;
        Bill storage b = bills[billId];
        b.merchant = t.merchant;
        b.buyer = t.buyer;
        b.arbiter = t.escrow ? t.arbiter : address(0);
        b.expiry = t.expiry;
        b.splitAllowed = t.splitAllowed;
        b.escrow = t.escrow;
        b.escrowTimeout = t.escrowTimeout == 0 ? DEFAULT_ESCROW_TIMEOUT : t.escrowTimeout;
        b.minContributionBps = t.minContributionBps;
        b.orderHash = t.orderHash;
        b.claimSigner = payer == address(0) ? claimSigner : address(0);

        for (uint256 i; i < t.offers.length; ++i) {
            Offer calldata o = t.offers[i];
            if (!tokenAllowed[o.token]) revert TokenNotAllowed();
            if (o.amount == 0 || offerAmount[billId][o.token] != 0) revert BadOffers(); // no zero price, no duplicates
            offerAmount[billId][o.token] = o.amount;
            emit BillOffer(billId, o.token, o.amount);
        }

        _mint(payer == address(0) ? address(this) : payer, billId);
        emit BillCreated(billId, t.merchant, payer, t.orderHash, t.escrow, t.expiry);
    }

    /// EIP-712 digest of the terms (arrays of structs hash as keccak256 of the concatenated struct hashes).
    function termsDigest(Terms calldata t) public view returns (bytes32) {
        bytes32[] memory oh = new bytes32[](t.offers.length);
        for (uint256 i; i < t.offers.length; ++i) {
            oh[i] = keccak256(abi.encode(OFFER_TYPEHASH, t.offers[i].token, t.offers[i].amount));
        }
        bytes32 offersHash = keccak256(abi.encodePacked(oh));
        bytes memory head = abi.encode(TERMS_TYPEHASH, t.merchant, t.buyer, t.arbiter, offersHash);
        bytes memory tail = abi.encode(t.expiry, t.orderHash, t.splitAllowed, t.minContributionBps, t.escrow, t.escrowTimeout, t.nonce);
        return _hashTypedDataV4(keccak256(bytes.concat(head, tail)));
    }

    // ------------------------------------------------------------------ claim link (F3)

    /// @notice The claim key signs (contract, chainId, billId, to). Copying the tx cannot
    ///         redirect the NFT because `to` is inside the signature.
    function claim(uint256 billId, address to, bytes calldata claimSig) external {
        Bill storage b = bills[billId];
        if (b.status != Status.Open || ownerOf(billId) != address(this) || b.claimSigner == address(0)) revert NotAllowed();
        bytes32 h = MessageHashUtils.toEthSignedMessageHash(
            keccak256(abi.encode(address(this), block.chainid, billId, to))
        );
        if (ECDSA.recover(h, claimSig) != b.claimSigner) revert BadSignature();
        b.claimSigner = address(0);
        _transfer(address(this), to, billId);
        emit BillClaimed(billId, to);
    }

    // ------------------------------------------------------------------ pay (F4 to F7)

    /// @notice Anyone may pay. The first payment picks the coin from the merchant's offers;
    ///         later split payments must use the same coin. ERC-20 needs a prior approve or a
    ///         permit (see payWithPermit TODO).
    function pay(uint256 billId, address coin, uint256 amount) external payable nonReentrant {
        Bill storage b = bills[billId];
        if (b.status != Status.Open) revert NotOpen();
        if (block.timestamp >= b.expiry) revert Expired();

        if (!b.tokenChosen) {
            uint256 price = offerAmount[billId][coin];
            if (price == 0) revert WrongCoin();
            b.token = coin;
            b.amount = price;
            b.tokenChosen = true;
            emit BillCoinPicked(billId, coin, price);
        } else if (coin != b.token) {
            revert WrongCoin();
        }

        uint256 remaining = b.amount - b.funded;
        if (amount == 0 || amount > remaining) revert BadAmount();                      // F7
        if (!b.splitAllowed && amount != remaining) revert BadAmount();
        if (b.splitAllowed && amount != remaining && amount * 10_000 < uint256(b.minContributionBps) * b.amount) revert BadAmount();

        // effects
        contributed[billId][msg.sender] += amount;
        b.funded += amount;
        bool settles = (b.funded == b.amount);
        if (settles) b.status = b.escrow ? Status.Held : Status.Paid;

        // interactions
        if (b.token == address(0)) {
            if (msg.value != amount) revert BadAmount();
        } else {
            if (msg.value != 0) revert BadAmount();
            IERC20(b.token).safeTransferFrom(msg.sender, address(this), amount);
        }
        emit BillContribution(billId, msg.sender, amount, b.funded);

        if (settles) {                                                                   // F6
            if (b.escrow) {
                b.heldUntil = uint64(block.timestamp) + b.escrowTimeout;
                emit BillHeld(billId, b.amount);
            } else {
                _send(b.token, b.merchant, b.amount);
                emit BillPaid(billId, b.merchant, b.amount);
            }
        }
    }

    // ------------------------------------------------------------------ escrow mode (5.2, core.md E2 to E4)

    /// @notice Buyer and merchant each approve; the second approval pays the merchant.
    ///         Both may approve at any time after full funding ("finalize early").
    function approveRelease(uint256 billId) external nonReentrant {
        Bill storage b = bills[billId];
        if (b.status != Status.Held) revert NotAllowed();
        if (msg.sender == b.buyer) b.buyerReleased = true;
        else if (msg.sender == b.merchant) b.merchantReleased = true;
        else revert NotAllowed();
        emit BillReleaseApproved(billId, msg.sender);
        if (b.buyerReleased && b.merchantReleased) {
            b.status = Status.Paid;
            _send(b.token, b.merchant, b.amount);
            emit BillPaid(billId, b.merchant, b.amount);
        }
    }

    /// @notice The arbiter settles a dispute: pay the merchant, or refund the payers (they then withdraw).
    function rule(uint256 billId, bool toMerchant) external nonReentrant {
        Bill storage b = bills[billId];
        if (b.status != Status.Held || msg.sender != b.arbiter) revert NotAllowed();
        emit BillRuled(billId, toMerchant);
        if (toMerchant) {
            b.status = Status.Paid;
            _send(b.token, b.merchant, b.amount);
            emit BillPaid(billId, b.merchant, b.amount);
        } else {
            b.status = Status.Refunded;
            emit BillRefunded(billId);
        }
    }

    // TODO payWithPermit (ERC-2612 / Permit2) and payWithAuthorization (ERC-3009, USDC)
    //      so a payer with no ETH can pay through a relayer or ERC-4337 paymaster (N6).

    // ------------------------------------------------------------------ cancel, refund, withdraw (F8 to F10)

    function cancel(uint256 billId) external {
        Bill storage b = bills[billId];
        if (b.status != Status.Open) revert NotOpen();
        if (msg.sender != b.buyer && msg.sender != b.merchant) revert NotAllowed();
        b.status = Status.Cancelled;
        emit BillCancelled(billId, msg.sender);
    }

    /// @notice Merchant refunds; contributors then withdraw their own share. A paid bill needs
    ///         the merchant to send the full amount back in; a held (escrow) bill already has it.
    function refund(uint256 billId) external payable nonReentrant {
        Bill storage b = bills[billId];
        if (msg.sender != b.merchant) revert NotAllowed();
        if (b.status == Status.Held) {
            if (msg.value != 0) revert BadAmount();
            b.status = Status.Refunded;
            emit BillRefunded(billId);
            return;
        }
        if (b.status != Status.Paid) revert NotAllowed();
        b.status = Status.Refunded;
        if (b.token == address(0)) {
            if (msg.value != b.amount) revert BadAmount();
        } else {
            if (msg.value != 0) revert BadAmount();
            IERC20(b.token).safeTransferFrom(msg.sender, address(this), b.amount);
        }
        emit BillRefunded(billId);
    }

    /// @notice Pull pattern: each contributor takes back exactly what they put in.
    ///         A held (escrow) bill nobody released or ruled on by heldUntil becomes refunded here.
    function withdraw(uint256 billId) external nonReentrant {
        Bill storage b = bills[billId];
        if (b.status == Status.Held && block.timestamp >= b.heldUntil) {
            b.status = Status.Refunded;
            emit BillRefunded(billId);
        }
        bool open_expired = (b.status == Status.Open && block.timestamp >= b.expiry);
        if (!(open_expired || b.status == Status.Cancelled || b.status == Status.Refunded)) revert NotExpiredOrClosed();
        uint256 amt = contributed[billId][msg.sender];
        if (amt == 0) revert NothingToWithdraw();
        contributed[billId][msg.sender] = 0;
        if (b.status != Status.Refunded) b.funded -= amt; // keeps invariant 1 for unsettled bills
        _send(b.token, msg.sender, amt);
        emit Withdrawn(billId, msg.sender, amt);
    }

    // ------------------------------------------------------------------ views

    function isExpired(uint256 billId) external view returns (bool) {
        Bill storage b = bills[billId];
        return b.status == Status.Open && block.timestamp >= b.expiry;
    }

    /// ERC-5192 style: a bill is locked (receipt) once it is no longer open.
    function locked(uint256 billId) external view returns (bool) {
        return bills[billId].status != Status.Open;
    }

    // TODO tokenURI: on chain JSON (merchant, amount, token, status, orderHash), no personal data.

    // ------------------------------------------------------------------ internals

    /// Bills can be passed on while Open ("ask my dad"); receipts cannot be traded.
    function _update(address to, uint256 tokenId, address auth) internal override returns (address from) {
        from = super._update(to, tokenId, auth);
        if (from != address(0) && to != address(0) && bills[tokenId].status != Status.Open) revert Locked();
    }

    function _send(address token, address to, uint256 amount) private {
        if (token == address(0)) {
            (bool ok, ) = to.call{value: amount}("");
            require(ok, "ETH send failed"); // a merchant that rejects ETH blocks settlement; prefer USDC
        } else {
            IERC20(token).safeTransfer(to, amount);
        }
    }
}
