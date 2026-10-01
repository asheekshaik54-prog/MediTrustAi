"""Compile + deploy to Ganache: python -m blockchain.deploy  (Ganache at http://127.0.0.1:8545)"""
import json, os
from solcx import compile_source, install_solc
from web3 import Web3
D = os.path.dirname(__file__)
install_solc("0.8.19")
src = open(os.path.join(D, "contracts", "ModelRegistry.sol")).read()
c = compile_source(src, solc_version="0.8.19", output_values=["abi", "bin"])["<stdin>:ModelRegistry"]
w3 = Web3(Web3.HTTPProvider(os.getenv("GANACHE_URL", "http://127.0.0.1:8545")))
acct = w3.eth.accounts[0]
tx = w3.eth.contract(abi=c["abi"], bytecode=c["bin"]).constructor().transact({"from": acct})
addr = w3.eth.wait_for_transaction_receipt(tx).contractAddress
json.dump({"address": addr, "abi": c["abi"]}, open(os.path.join(D, "deployed.json"), "w"), indent=2)
print("Deployed at", addr)
