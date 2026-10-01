"""Hospital edge node: python -m federated.client --id 0"""
import argparse, flwr as fl, numpy as np
from ai_model.common import *

def partition(X, y, hid, n=3):
    idx = np.array_split(np.random.default_rng(7).permutation(len(X)), n)[hid]
    return X[idx], y[idx]

class Hospital(fl.client.NumPyClient):
    def __init__(self, hid):
        Xtr, self.Xte, ytr, self.yte, _ = get_splits()
        self.X, self.y = partition(Xtr, ytr, hid)   # data never leaves this node
        self.model = build_model()
    def get_parameters(self, config): return self.model.get_weights()
    def fit(self, params, config):
        self.model.set_weights(params)
        self.model.fit(self.X, self.y, epochs=3, batch_size=32, verbose=0)
        return self.model.get_weights(), len(self.X), {}
    def evaluate(self, params, config):
        self.model.set_weights(params)
        loss, acc = self.model.evaluate(self.Xte, self.yte, verbose=0)
        return float(loss), len(self.Xte), {"accuracy": float(acc)}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--id", type=int, required=True)
    ap.add_argument("--server", default="127.0.0.1:8080"); a = ap.parse_args()
    fl.client.start_numpy_client(server_address=a.server, client=Hospital(a.id))
