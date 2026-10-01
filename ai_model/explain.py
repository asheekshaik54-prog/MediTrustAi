"""SHAP explanations for a single patient."""
import numpy as np, shap
from ai_model.common import FEATURES

class Explainer:
    def __init__(self, model, background):
        f = lambda x: model.predict(x, verbose=0).ravel()
        self.exp = shap.KernelExplainer(f, shap.sample(background, 50))
    def explain(self, x_scaled):
        sv = np.array(self.exp.shap_values(x_scaled, nsamples=100)).reshape(-1)
        mx = np.abs(sv).max() or 1
        out = []
        for name, v in zip(FEATURES, sv):
            r = abs(v)/mx
            out.append({"feature": name, "shap": float(v),
                        "impact": "High" if r > .66 else "Medium" if r > .33 else "Low"})
        return sorted(out, key=lambda d: -abs(d["shap"]))
