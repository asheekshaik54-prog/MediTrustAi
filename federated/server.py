"""Flower server with FedAvg; after each round saves weights, SHA-256 hashes them, logs on blockchain."""
import os, json, time, hashlib, numpy as np, flwr as fl
from ai_model.common import ART
from blockchain.client import ChainClient

class VerifiedFedAvg(fl.server.strategy.FedAvg):
    def __init__(self, **kw):
        super().__init__(**kw); self.chain = ChainClient(); self.history = []
    def aggregate_fit(self, rnd, results, failures):
        params, m = super().aggregate_fit(rnd, results, failures)
        if params is not None:
            arrs = fl.common.parameters_to_ndarrays(params)
            os.makedirs(ART, exist_ok=True)
            np.savez(os.path.join(ART, "global_model.npz"), *arrs)
            h = hashlib.sha256(b"".join(a.tobytes() for a in arrs)).hexdigest()
            rec = self.chain.register_model(f"v{rnd}", "FEDERATED_SERVER", h)
            self.history.append({"version": f"v{rnd}", "hash": h, "timestamp": time.time(), **rec})
            json.dump(self.history, open(os.path.join(ART, "model_history.json"), "w"), indent=2)
            print(f"[round {rnd}] model hash {h[:16]}... stored ({rec['mode']})")
        return params, m

def wavg(metrics):
    n = sum(c for c, _ in metrics)
    return {"accuracy": sum(c*m["accuracy"] for c, m in metrics)/n}

if __name__ == "__main__":
    strat = VerifiedFedAvg(min_fit_clients=3, min_available_clients=3, min_evaluate_clients=3,
                           evaluate_metrics_aggregation_fn=wavg)
    fl.server.start_server(server_address="0.0.0.0:8080",
                           config=fl.server.ServerConfig(num_rounds=5), strategy=strat)
