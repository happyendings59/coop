// Tests for BillTo.sol. Runs on an in-process Ganache chain, no network needed.
// Requirement IDs (F1..F12) and invariants (INV1..INV6) refer to spec/bill-to.md.
const { test, beforeEach } = require("node:test");
const assert = require("node:assert/strict");
const ganache = require("ganache");
const { ethers } = require("ethers");
const art = require("../build/artifacts.json");

const CHAIN_ID = 1337;
const U = (n) => ethers.parseUnits(String(n), 18);
const KEYS = Array.from({ length: 9 }, (_, i) => ethers.zeroPadValue(ethers.toBeHex(i + 1), 32));

let provider, admin, merchant, buyer, alice, bob, carol, dave, stranger, arbiter;
let billto, token, other;

async function deploy(name, signer, ...args) {
  const f = new ethers.ContractFactory(art[name].abi, art[name].bytecode, signer);
  const c = await f.deploy(...args);
  await c.waitForDeployment();
  return c;
}

async function increaseTime(sec) {
  await provider.send("evm_increaseTime", [sec]);
  await provider.send("evm_mine", []);
}

async function now() {
  return (await provider.getBlock("latest")).timestamp;
}

async function expectRevert(p, errorName) {
  try {
    const tx = await p;
    if (tx && tx.wait) await tx.wait();
  } catch (e) {
    const data = e?.data ?? e?.info?.error?.data?.result ?? e?.info?.error?.data;
    if (errorName) {
      let name;
      try { name = billto.interface.parseError(data)?.name; } catch {}
      if (!name) try { name = token.interface.parseError(data)?.name; } catch {}
      const msg = String(e.shortMessage || e.message || "");
      assert.ok(name === errorName || msg.includes(errorName), `expected ${errorName}, got ${name || msg}`);
    }
    return;
  }
  assert.fail(`expected revert${errorName ? " " + errorName : ""}`);
}

let nonce = 0;
async function makeTerms(over = {}) {
  const t = {
    merchant: merchant.address,
    buyer: buyer.address,
    arbiter: ethers.ZeroAddress,
    offers: [{ token: await token.getAddress(), amount: U(100) }],
    expiry: (await now()) + 3600,
    orderHash: ethers.keccak256(ethers.toUtf8Bytes(`order-${nonce}`)),
    splitAllowed: false,
    minContributionBps: 0,
    escrow: false,
    nonce: nonce++,
    ...over,
  };
  const domain = { name: "BillTo", version: "1", chainId: CHAIN_ID, verifyingContract: await billto.getAddress() };
  const types = {
    Terms: [
      { name: "merchant", type: "address" }, { name: "buyer", type: "address" }, { name: "arbiter", type: "address" },
      { name: "offers", type: "Offer[]" }, { name: "expiry", type: "uint64" }, { name: "orderHash", type: "bytes32" },
      { name: "splitAllowed", type: "bool" }, { name: "minContributionBps", type: "uint16" }, { name: "escrow", type: "bool" },
      { name: "nonce", type: "uint256" },
    ],
    Offer: [{ name: "token", type: "address" }, { name: "amount", type: "uint256" }],
  };
  const signer = over.signer || merchant;
  delete t.signer;
  const sig = await signer.signTypedData(domain, types, t);
  return { t, sig };
}

async function createBill(over = {}, payer, claimSigner = ethers.ZeroAddress) {
  const { t, sig } = await makeTerms(over);
  const id = await billto.nextBillId();
  await (await billto.connect(buyer).createBill(t, sig, payer ?? alice.address, claimSigner)).wait();
  return { id, t };
}

async function pay(who, id, amt, coin = token) {
  await (await coin.connect(who).approve(await billto.getAddress(), amt)).wait();
  return billto.connect(who).pay(id, await coin.getAddress(), amt);
}

const bal = async (a) => token.balanceOf(a.address ?? a);
const status = async (id) => Number((await billto.bills(id)).status); // 0 Open 1 Held 2 Paid 3 Cancelled 4 Refunded
const OPEN = 0, HELD = 1, PAID = 2, CANCELLED = 3, REFUNDED = 4;

beforeEach(async () => {
  const g = ganache.provider({
    logging: { quiet: true },
    chain: { chainId: CHAIN_ID },
    miner: { instamine: "eager" },
    wallet: { accounts: KEYS.map((k) => ({ secretKey: k, balance: ethers.toBeHex(U(1000)) })) },
  });
  provider = new ethers.BrowserProvider(g, undefined, { cacheTimeout: -1, pollingInterval: 10 });
  provider.pollingInterval = 10;
  // Plain wallets (no NonceManager): a reverted send must not leave a nonce gap.
  [admin, merchant, buyer, alice, bob, carol, dave, stranger, arbiter] = KEYS.map((k) => new ethers.Wallet(k, provider));
  billto = await deploy("BillTo", admin, admin.address);
  token = await deploy("MockERC20", admin);
  other = await deploy("MockERC20", admin);
  await (await billto.connect(admin).setToken(await token.getAddress(), true)).wait();
  for (const s of [alice, bob, carol, dave, merchant, stranger]) await (await token.connect(admin).mint(s.address, U(1000))).wait();
});

test("F1 F2 F6: one payer pays in full, merchant paid at once, NFT locks as receipt", async () => {
  const { id } = await createBill();
  assert.equal(await billto.ownerOf(id), alice.address);
  const before = await bal(merchant);
  await (await pay(alice, id, U(100))).wait();
  assert.equal(await bal(merchant) - before, U(100));
  assert.equal(await status(id), PAID);
  assert.equal(await billto.locked(id), true);
  assert.equal(await bal(await billto.getAddress()), 0n); // INV1
  await expectRevert(billto.connect(alice).transferFrom(alice.address, bob.address, id), "Locked");
});

test("F4: anyone may pay, not only the NFT holder", async () => {
  const { id } = await createBill();
  await (await pay(bob, id, U(100))).wait();
  assert.equal(await status(id), PAID);
});

test("F5 F6: Uber style split, four payers, last one settles", async () => {
  const { id } = await createBill({ splitAllowed: true, minContributionBps: 1000 });
  const before = await bal(merchant);
  for (const p of [alice, bob, carol]) await (await pay(p, id, U(25))).wait();
  assert.equal(await status(id), OPEN);
  assert.equal(await bal(await billto.getAddress()), U(75)); // INV1 while open
  await (await pay(dave, id, U(25))).wait();
  assert.equal(await status(id), PAID);
  assert.equal(await bal(merchant) - before, U(100));
  assert.equal(await bal(await billto.getAddress()), 0n);
});

test("F5: split refuses contributions under the minimum unless it finishes the bill", async () => {
  const { id } = await createBill({ splitAllowed: true, minContributionBps: 1000 });
  await expectRevert(pay(alice, id, U(5)), "BadAmount");
  await (await pay(alice, id, U(95))).wait();
  await (await pay(bob, id, U(5))).wait(); // under min but exactly the remainder
  assert.equal(await status(id), PAID);
});

test("F5: no split means partial payment is refused", async () => {
  const { id } = await createBill();
  await expectRevert(pay(alice, id, U(50)), "BadAmount");
});

test("F7 INV3: overpayment is refused", async () => {
  const { id } = await createBill({ splitAllowed: true });
  await expectRevert(pay(alice, id, U(101)), "BadAmount");
  await (await pay(alice, id, U(60))).wait();
  await expectRevert(pay(bob, id, U(41)), "BadAmount");
});

test("F8 INV4: expiry, no more pay, each contributor withdraws only their own", async () => {
  const { id } = await createBill({ splitAllowed: true });
  await (await pay(alice, id, U(30))).wait();
  await (await pay(bob, id, U(20))).wait();
  await expectRevert(billto.connect(alice).withdraw(id), "NotExpiredOrClosed");
  await increaseTime(3601);
  assert.equal(await billto.isExpired(id), true);
  await expectRevert(pay(carol, id, U(50)), "Expired");
  const a0 = await bal(alice), b0 = await bal(bob);
  await (await billto.connect(alice).withdraw(id)).wait();
  await (await billto.connect(bob).withdraw(id)).wait();
  assert.equal(await bal(alice) - a0, U(30));
  assert.equal(await bal(bob) - b0, U(20));
  await expectRevert(billto.connect(alice).withdraw(id), "NothingToWithdraw");
  await expectRevert(billto.connect(stranger).withdraw(id), "NothingToWithdraw");
  assert.equal(await bal(await billto.getAddress()), 0n);
});

test("F9: buyer or merchant cancels; stranger cannot; contributors withdraw", async () => {
  const { id } = await createBill({ splitAllowed: true });
  await (await pay(alice, id, U(40))).wait();
  await expectRevert(billto.connect(stranger).cancel(id), "NotAllowed");
  await (await billto.connect(buyer).cancel(id)).wait();
  assert.equal(await status(id), CANCELLED);
  await expectRevert(pay(bob, id, U(60)), "NotOpen");
  const a0 = await bal(alice);
  await (await billto.connect(alice).withdraw(id)).wait();
  assert.equal(await bal(alice) - a0, U(40));

  const { id: id2 } = await createBill();
  await (await billto.connect(merchant).cancel(id2)).wait();
  assert.equal(await status(id2), CANCELLED);
});

test("F10: merchant refunds a paid bill; contributors get back what they paid", async () => {
  const { id } = await createBill({ splitAllowed: true });
  await (await pay(alice, id, U(70))).wait();
  await (await pay(bob, id, U(30))).wait();
  await expectRevert(billto.connect(stranger).refund(id), "NotAllowed");
  await (await token.connect(merchant).approve(await billto.getAddress(), U(100))).wait();
  await (await billto.connect(merchant).refund(id)).wait();
  assert.equal(await status(id), REFUNDED);
  const a0 = await bal(alice), b0 = await bal(bob);
  await (await billto.connect(alice).withdraw(id)).wait();
  await (await billto.connect(bob).withdraw(id)).wait();
  assert.equal(await bal(alice) - a0, U(70));
  assert.equal(await bal(bob) - b0, U(30));
  assert.equal(await bal(await billto.getAddress()), 0n);
  await expectRevert(billto.connect(merchant).refund(id), "NotAllowed"); // INV2: no double refund
});

test("F3: claim link over SimpleX or Telegram; a copied claim cannot be redirected", async () => {
  const claimKey = ethers.Wallet.createRandom();
  const { id } = await createBill({}, ethers.ZeroAddress, claimKey.address);
  assert.equal(await billto.ownerOf(id), await billto.getAddress());
  const sign = (to) => claimKey.signMessage(ethers.getBytes(ethers.keccak256(
    ethers.AbiCoder.defaultAbiCoder().encode(["address", "uint256", "uint256", "address"], [
      billto.target, CHAIN_ID, id, to]))));
  const sigForCarol = await sign(carol.address);
  // Attacker copies Carol's signature but names himself.
  await expectRevert(billto.connect(stranger).claim(id, stranger.address, sigForCarol), "BadSignature");
  // Anyone may submit Carol's claim; the NFT still goes to Carol.
  await (await billto.connect(stranger).claim(id, carol.address, sigForCarol)).wait();
  assert.equal(await billto.ownerOf(id), carol.address);
  await expectRevert(billto.connect(carol).claim(id, carol.address, sigForCarol), "NotAllowed"); // one use
});

test("F1 INV6: bad merchant signature, reused terms, and unlisted coin are refused", async () => {
  const forged = await makeTerms({ signer: stranger });
  await expectRevert(billto.connect(buyer).createBill(forged.t, forged.sig, alice.address, ethers.ZeroAddress), "BadSignature");
  const ok = await makeTerms();
  await (await billto.connect(buyer).createBill(ok.t, ok.sig, alice.address, ethers.ZeroAddress)).wait();
  await expectRevert(billto.connect(buyer).createBill(ok.t, ok.sig, alice.address, ethers.ZeroAddress), "TermsReused");
  const unlisted = await makeTerms({ offers: [{ token: await other.getAddress(), amount: U(100) }] });
  await expectRevert(billto.connect(buyer).createBill(unlisted.t, unlisted.sig, alice.address, ethers.ZeroAddress), "TokenNotAllowed");
  const past = await makeTerms({ expiry: (await now()) - 1 });
  await expectRevert(billto.connect(buyer).createBill(past.t, past.sig, alice.address, ethers.ZeroAddress), "BadAmount");
});

test("Options: a second coin can be allowlisted and used (BOLD default, others allowed)", async () => {
  await (await billto.connect(admin).setToken(await other.getAddress(), true)).wait();
  await expectRevert(billto.connect(stranger).setToken(await other.getAddress(), false));
  await (await other.connect(admin).mint(alice.address, U(100))).wait();
  const { id } = await createBill({ offers: [{ token: await other.getAddress(), amount: U(100) }] });
  await (await pay(alice, id, U(100), other)).wait();
  assert.equal(await other.balanceOf(merchant.address), U(100));
});

test("Open bill can be passed on (ask my dad); paid bill cannot", async () => {
  const { id } = await createBill();
  await (await billto.connect(alice).transferFrom(alice.address, dave.address, id)).wait();
  assert.equal(await billto.ownerOf(id), dave.address);
});

test("Freeze simulation: frozen merchant blocks settlement, contributors still get money back", async () => {
  const { id } = await createBill({ splitAllowed: true });
  await (await pay(alice, id, U(50))).wait();
  await (await token.connect(admin).freeze(merchant.address, true)).wait();
  await expectRevert(pay(bob, id, U(50))); // final payment reverts as a whole
  assert.equal(await status(id), OPEN);
  await increaseTime(3601);
  const a0 = await bal(alice);
  await (await billto.connect(alice).withdraw(id)).wait();
  assert.equal(await bal(alice) - a0, U(50));
});

// ---------------------------------------------------------------- payer picks the coin (F11, 5.5)

test("F11: merchant offers several coins at their own prices; the first payer picks one", async () => {
  await (await billto.connect(admin).setToken(await other.getAddress(), true)).wait();
  await (await other.connect(admin).mint(alice.address, U(1000))).wait();
  const offers = [{ token: await token.getAddress(), amount: U(100) }, { token: await other.getAddress(), amount: 100_000_000n }]; // e.g. 18 vs 6 decimals
  const { id } = await createBill({ offers, splitAllowed: true, minContributionBps: 1000 });
  const third = await deploy("MockERC20", admin);
  await (await third.connect(admin).mint(alice.address, U(100))).wait();
  await expectRevert(pay(alice, id, U(100), third), "WrongCoin"); // never offered
  await (await pay(alice, id, 60_000_000n, other)).wait(); // Alice picks the second coin
  const b = await billto.bills(id);
  assert.equal(b.token, await other.getAddress());
  assert.equal(b.amount, 100_000_000n);
  await expectRevert(pay(bob, id, U(40), token), "WrongCoin"); // split must stay in the picked coin
  await (await other.connect(admin).mint(bob.address, U(1000))).wait();
  await (await pay(bob, id, 40_000_000n, other)).wait();
  assert.equal(await status(id), PAID);
  assert.equal(await other.balanceOf(merchant.address), 100_000_000n);
});

test("F11: offers must be 1 to 4 allowlisted coins, no duplicates, no zero price", async () => {
  const tk = await token.getAddress();
  const tries = [
    { offers: [] },
    { offers: [1, 2, 3, 4, 5].map((n) => ({ token: tk, amount: U(n) })) },
    { offers: [{ token: tk, amount: U(1) }, { token: tk, amount: U(2) }] },
    { offers: [{ token: tk, amount: 0n }] },
  ];
  for (const over of tries) {
    const x = await makeTerms(over);
    await expectRevert(billto.connect(buyer).createBill(x.t, x.sig, alice.address, ethers.ZeroAddress), "BadOffers");
  }
});

test("F11: native ETH can be offered and paid", async () => {
  await (await billto.connect(admin).setToken(ethers.ZeroAddress, true)).wait();
  const { id } = await createBill({ offers: [{ token: ethers.ZeroAddress, amount: U(1) }] });
  const before = await provider.getBalance(merchant.address);
  await (await billto.connect(alice).pay(id, ethers.ZeroAddress, U(1), { value: U(1) })).wait();
  assert.equal(await provider.getBalance(merchant.address) - before, U(1));
  assert.equal(await status(id), PAID);
});

// ---------------------------------------------------------------- escrow mode (5.2, core.md E2 to E4)

const esc = () => ({ escrow: true, arbiter: arbiter.address });

test("Escrow: full funding holds the money; both sides release (finalize early); merchant paid", async () => {
  const { id } = await createBill(esc());
  const before = await bal(merchant);
  await (await pay(alice, id, U(100))).wait();
  assert.equal(await status(id), HELD);
  assert.equal(await bal(await billto.getAddress()), U(100));
  await expectRevert(billto.connect(stranger).approveRelease(id), "NotAllowed");
  await (await billto.connect(merchant).approveRelease(id)).wait();
  assert.equal(await status(id), HELD); // one side is not enough
  await (await billto.connect(buyer).approveRelease(id)).wait();
  assert.equal(await status(id), PAID);
  assert.equal(await bal(merchant) - before, U(100));
  assert.equal(await bal(await billto.getAddress()), 0n);
  assert.equal(await billto.locked(id), true);
});

test("Escrow: a held bill does not expire and cannot be withdrawn or cancelled", async () => {
  const { id } = await createBill(esc());
  await (await pay(alice, id, U(100))).wait();
  await increaseTime(3601);
  await expectRevert(billto.connect(alice).withdraw(id), "NotExpiredOrClosed");
  await expectRevert(billto.connect(buyer).cancel(id), "NotOpen");
  assert.equal(await status(id), HELD);
});

test("Escrow: arbiter rules for the merchant, or refunds the payers; nobody else can rule", async () => {
  const { id } = await createBill({ ...esc(), splitAllowed: true });
  await (await pay(alice, id, U(70))).wait();
  await (await pay(bob, id, U(30))).wait();
  await expectRevert(billto.connect(merchant).rule(id, true), "NotAllowed");
  const a0 = await bal(alice), b0 = await bal(bob);
  await (await billto.connect(arbiter).rule(id, false)).wait();
  assert.equal(await status(id), REFUNDED);
  await (await billto.connect(alice).withdraw(id)).wait();
  await (await billto.connect(bob).withdraw(id)).wait();
  assert.equal(await bal(alice) - a0, U(70));
  assert.equal(await bal(bob) - b0, U(30));
  assert.equal(await bal(await billto.getAddress()), 0n);
  await expectRevert(billto.connect(arbiter).rule(id, true), "NotAllowed"); // INV2: settled once

  const { id: id2 } = await createBill(esc());
  await (await pay(alice, id2, U(100))).wait();
  const m0 = await bal(merchant);
  await (await billto.connect(arbiter).rule(id2, true)).wait();
  assert.equal(await status(id2), PAID);
  assert.equal(await bal(merchant) - m0, U(100));
});

test("Escrow: merchant can refund a held bill without sending money in", async () => {
  const { id } = await createBill(esc());
  await (await pay(alice, id, U(100))).wait();
  await (await billto.connect(merchant).refund(id)).wait();
  assert.equal(await status(id), REFUNDED);
  const a0 = await bal(alice);
  await (await billto.connect(alice).withdraw(id)).wait();
  assert.equal(await bal(alice) - a0, U(100));
});

test("Escrow: needs an arbiter who is neither merchant nor buyer", async () => {
  for (const a of [ethers.ZeroAddress, merchant.address, buyer.address]) {
    const x = await makeTerms({ escrow: true, arbiter: a });
    await expectRevert(billto.connect(buyer).createBill(x.t, x.sig, alice.address, ethers.ZeroAddress), "BadArbiter");
  }
});
