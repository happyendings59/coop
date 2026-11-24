// Compiles BillTo.sol and the test mock with solc-js 0.8.24 and writes build/artifacts.json.
const solc = require("solc"), fs = require("fs"), path = require("path");
const files = ["BillTo.sol", "test/MockERC20.sol"];
const sources = Object.fromEntries(files.map(f => [f, { content: fs.readFileSync(f, "utf8") }]));
const input = { language: "Solidity", sources,
  settings: { viaIR: true, optimizer: { enabled: true, runs: 200 }, outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } } } };
const findImports = p => { try { return { contents: fs.readFileSync(path.join("node_modules", p), "utf8") }; } catch { return { error: "not found: " + p }; } };
const out = JSON.parse(solc.compile(JSON.stringify(input), { import: findImports }));
let bad = false;
for (const e of out.errors || []) { console.error(e.formattedMessage); if (e.severity === "error") bad = true; }
if (bad) process.exit(1);
const art = {};
for (const f of files) for (const [name, c] of Object.entries(out.contracts[f])) art[name] = { abi: c.abi, bytecode: "0x" + c.evm.bytecode.object };
fs.mkdirSync("build", { recursive: true });
fs.writeFileSync("build/artifacts.json", JSON.stringify(art));
console.log("compiled:", Object.keys(art).join(", "));
