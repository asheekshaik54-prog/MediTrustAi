"""Blockchain client. Falls back to a local hash-chained ledger if Ganache/contract is unavailable."""
import os, json, time, hashlib
from web3 import Web3
D = os.path.dirname(__file__)
LEDGER = os.path.join(D, "..", "artifacts", "local_ledger.json")

class ChainClient:
    def __init__(self):
        self.contract = None
        try:
            w3 = Web3(Web3.HTTPProvider(os.getenv("GANACHE_URL", "http://127.0.0.1:8545"),
                                        request_kwargs={"timeout": 3}))
            d = json.load(open(os.path.join(D, "deployed.json")))
            if w3.is_connected():
                self.w3, self.acct = w3, w3.eth.accounts[0]
                self.contract = w3.eth.contract(address=d["address"], abi=d["abi"])
        except Exception: pass

    @property
    def mode(self): return "ethereum" if self.contract else "local-ledger"

    def _ledger(self):
        return json.load(open(LEDGER)) if os.path.exists(LEDGER) else []

    def register_model(self, version, hospital_id, model_hash):
        if self.contract:
            tx = self.contract.functions.registerModel(version, hospital_id, model_hash).transact({"from": self.acct})
            r = self.w3.eth.wait_for_transaction_receipt(tx)
            return {"mode": "ethereum", "tx": r.transactionHash.hex()}
        led = self._ledger(); prev = led[-1]["block_hash"] if led else "0"*64
        rec = {"id": len(led), "version": version, "hospitalId": hospital_id, "modelHash": model_hash,
               "timestamp": int(time.time()), "prev": prev}
        rec["block_hash"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        json.dump(led + [rec], open(LEDGER, "w"), indent=2)
        return {"mode": "local-ledger", "tx": rec["block_hash"]}

    def records(self):
        if self.contract:
            n = self.contract.functions.count().call(); out = []
            for i in range(n):
                v, h, mh, ts = self.contract.functions.records(i).call()
                out.append({"id": i, "version": v, "hospitalId": h, "modelHash": mh, "timestamp": ts})
            return out
        return self._ledger()

    def verify(self, model_hash):
        """True if this hash was ever registered -> detects tampered model files."""
        return any(r["modelHash"] == model_hash for r in self.records())
