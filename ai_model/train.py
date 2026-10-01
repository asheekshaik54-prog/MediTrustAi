"""Centralised baseline: python -m ai_model.train"""
import os, json, joblib, time
from ai_model.common import *

def main():
    Xtr, Xte, ytr, yte, sc = get_splits()
    m = build_model(); m.fit(Xtr, ytr, epochs=40, batch_size=32, validation_split=0.1, verbose=0)
    t = time.time(); p = m.predict(Xte, verbose=0).ravel(); lat = (time.time()-t)/len(Xte)*1000
    res = metrics(yte, p); res["latency_ms_per_sample"] = lat
    os.makedirs(ART, exist_ok=True)
    m.save_weights(os.path.join(ART, "centralized.weights.h5"))
    joblib.dump(sc, os.path.join(ART, "scaler.pkl"))
    json.dump(res, open(os.path.join(ART, "centralized_metrics.json"), "w"), indent=2)
    print(res)
if __name__ == "__main__": main()
