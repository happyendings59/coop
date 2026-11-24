// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity ^0.8.24;

// SKETCH ONLY. Compiles clean with solc 0.8.24 + OpenZeppelin 5.0.2 (checked 2026-11-23).
// Not tested, not audited, not deployed.
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
///         claim link). Full funding pays the merchant in the same transaction.
contract BillTo is ERC721, EIP712, ReentrancyGuard, Ownable2Step {
    using SafeERC20 for IERC20;

    enum Status { Open, Paid, Cancelled, Refunded } // Expired is computed (Open && now >= expiry)

    /// Terms the merchant signs. token == address(0) means native ETH.
    struct Terms {
        address merchant;        // receives funds; EOA or ERC-1271 contract (e.g. a co-op Safe)
        address buyer;           // who may cancel along with the merchant
        address token;
        uint256 amount;
        uint64  expiry;          // unix seconds
        bytes32 orderHash;       // keccak256 of the merchant's order JSON (N5)
        bool    splitAllowed;
        uint256 minContribution; // ignored if !splitAllowed
        uint256 nonce;           // merchant chosen, one use
    }

    struct Bill {
        address merchant;
        address buyer;
        address token;
        uint64  expiry;
        Status  status;
        bool    splitAllowed;
        uint256 amount;
        uint256 funded;
        uint256 minContribution;
        bytes32 orderHash;
        address claimSigner;     // throwaway key from the claim link, or zero
    }

    bytes32 private constant TERMS_TYPEHASH = keccak256(
        "Terms(address merchant,address buyer,address token,uint256 amount,uint64 expiry,bytes32 orderHash,bool splitAllowed,uint256 minContribution,uint256 nonce)"
    );

    mapping(address => bool) public tokenAllowed;                         // F11
    mapping(bytes32 => bool) public termsUsed;                            // replay guard
    mapping(uint256 => Bill) public bills;
    mapping(uint256 => mapping(address => uint256)) public contributed;  // F5
    uint256 public nextBillId = 1;

    event BillCreated(uint256 indexed billId, address indexed merchant, address indexed payer, bytes32 orderHash, address token, uint256 amount, uint64 expiry);
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
        if (!tokenAllowed[t.token]) revert TokenNotAllowed();
        if (t.amount == 0 || t.expiry <= block.timestamp) revert BadAmount();
        if (payer == address(0) && claimSigner == address(0)) revert NotAllowed();

        bytes32 digest = _hashTypedDataV4(keccak256(abi.encode(
            TERMS_TYPEHASH, t.merchant, t.buyer, t.token, t.amount, t.expiry,
            t.orderHash, t.splitAllowed, t.minContribution, t.nonce
        )));
        if (termsUsed[digest]) revert TermsReused();
        if (!SignatureChecker.isValidSignatureNow(t.merchant, digest, merchantSig)) revert BadSignature();
        termsUsed[digest] = true;

        billId = nextBillId++;
        bills[billId] = Bill({
            merchant: t.merchant,
            buyer: t.buyer,
            token: t.token,
            expiry: t.expiry,
            status: Status.Open,
            splitAllowed: t.splitAllowed,
            amount: t.amount,
            funded: 0,
            minContribution: t.minContribution,
            orderHash: t.orderHash,
            claimSigner: payer == address(0) ? claimSigner : address(0)
        });

        _mint(payer == address(0) ? address(this) : payer, billId);
        emit BillCreated(billId, t.merchant, payer, t.orderHash, t.token, t.amount, t.expiry);
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

    /// @notice Anyone may pay. ERC-20 needs a prior approve or a permit (see payWithPermit TODO).
    function pay(uint256 billId, uint256 amount) external payable nonReentrant {
        Bill storage b = bills[billId];
        if (b.status != Status.Open) revert NotOpen();
        if (block.timestamp >= b.expiry) revert Expired();

        uint256 remaining = b.amount - b.funded;
        if (amount == 0 || amount > remaining) revert BadAmount();                      // F7
        if (!b.splitAllowed && amount != remaining) revert BadAmount();
        if (b.splitAllowed && amount < b.minContribution && amount != remaining) revert BadAmount();

        // effects
        contributed[billId][msg.sender] += amount;
        b.funded += amount;
        bool settles = (b.funded == b.amount);
        if (settles) b.status = Status.Paid;

        // interactions
        if (b.token == address(0)) {
            if (msg.value != amount) revert BadAmount();
        } else {
            if (msg.value != 0) revert BadAmount();
            IERC20(b.token).safeTransferFrom(msg.sender, address(this), amount);
        }
        emit BillContribution(billId, msg.sender, amount, b.funded);

        if (settles) {                                                                   // F6
            _send(b.token, b.merchant, b.amount);
            emit BillPaid(billId, b.merchant, b.amount);
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

    /// @notice Merchant returns the full amount; contributors then withdraw their own share.
    function refund(uint256 billId) external payable nonReentrant {
        Bill storage b = bills[billId];
        if (b.status != Status.Paid) revert NotAllowed();
        if (msg.sender != b.merchant) revert NotAllowed();
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
    function withdraw(uint256 billId) external nonReentrant {
        Bill storage b = bills[billId];
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
