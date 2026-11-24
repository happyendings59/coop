// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// Test token standing in for BOLD or USDC. Can blacklist an address to simulate an issuer freeze.
contract MockERC20 is ERC20 {
    mapping(address => bool) public frozen;
    constructor() ERC20("Mock BOLD", "mBOLD") {}
    function mint(address to, uint256 amt) external { _mint(to, amt); }
    function freeze(address who, bool f) external { frozen[who] = f; }
    function _update(address from, address to, uint256 v) internal override {
        require(!frozen[from] && !frozen[to], "frozen");
        super._update(from, to, v);
    }
}
