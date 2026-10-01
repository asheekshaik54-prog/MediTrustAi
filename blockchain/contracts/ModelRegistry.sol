// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ModelRegistry {
    struct Record { string version; string hospitalId; string modelHash; uint256 timestamp; }
    Record[] public records;
    event ModelRegistered(uint256 indexed id, string version, string hospitalId, string modelHash, uint256 timestamp);

    function registerModel(string memory version, string memory hospitalId, string memory modelHash) public returns (uint256) {
        records.push(Record(version, hospitalId, modelHash, block.timestamp));
        emit ModelRegistered(records.length - 1, version, hospitalId, modelHash, block.timestamp);
        return records.length - 1;
    }
    function count() public view returns (uint256) { return records.length; }
    function verify(uint256 id, string memory modelHash) public view returns (bool) {
        return keccak256(bytes(records[id].modelHash)) == keccak256(bytes(modelHash));
    }
}
