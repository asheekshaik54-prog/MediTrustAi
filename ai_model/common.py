"""Shared data + model utilities (used by training, federated clients, backend)."""
import os, numpy as np, pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

FEATURES = ["age", "sex", "cp", "trestbps", "chol", "thalach", "restecg"]
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "heart.csv")
ART = os.path.join(os.path.dirname(__file__), "..", "artifacts")

def load_data(seed=42):
    """Loads UCI Heart Disease CSV (columns: FEATURES + 'target'); else synthetic data."""
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)[FEATURES + ["target"]].dropna()
        df["target"] = (df["target"] > 0).astype(int)
    else:
        rng = np.random.default_rng(seed); n = 1200
        df = pd.DataFrame({
            "age": rng.integers(29, 78, n), "sex": rng.integers(0, 2, n),
            "cp": rng.integers(0, 4, n), "trestbps": rng.normal(131, 17, n),
            "chol": rng.normal(246, 51, n), "thalach": rng.normal(150, 23, n),
            "restecg": rng.integers(0, 3, n)})
        z = (0.04*(df.age-54) + 0.015*(df.trestbps-131) + 0.01*(df.chol-246)
             - 0.03*(df.thalach-150) + 0.5*df.restecg + 0.4*(df.cp > 0) + 0.5*df.sex
             + rng.normal(0, 0.8, n))
        df["target"] = (z > 0.3).astype(int)
    return df

def get_splits(seed=42):
    df = load_data(seed)
    X, y = df[FEATURES].values.astype("float32"), df["target"].values.astype("float32")
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)
    sc = StandardScaler().fit(Xtr)
    return sc.transform(Xtr).astype("float32"), sc.transform(Xte).astype("float32"), ytr, yte, sc

def build_model(n_features=len(FEATURES)):
    m = tf.keras.Sequential([
        tf.keras.layers.Input((n_features,)),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid")])
    m.compile("adam", "binary_crossentropy", metrics=["accuracy"])
    return m

def metrics(y, p):
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    yh = (p > 0.5).astype(int)
    return dict(accuracy=accuracy_score(y, yh), precision=precision_score(y, yh, zero_division=0),
                recall=recall_score(y, yh), f1=f1_score(y, yh), roc_auc=roc_auc_score(y, p))
