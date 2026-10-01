"""FastAPI backend: uvicorn backend.main:app --reload"""
import os, time, hashlib, joblib, numpy as np
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from pymongo import MongoClient
from bson import ObjectId

from ai_model.common import FEATURES, ART, build_model, get_splits
from ai_model.explain import Explainer
from blockchain.client import ChainClient

SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
db = MongoClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))["meditrust"]
pwd = CryptContext(schemes=["bcrypt"]); oauth = OAuth2PasswordBearer(tokenUrl="auth/login")
chain = ChainClient()
app = FastAPI(title="MediTrust AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---- model loading (federated global model preferred; verified against blockchain) ----
_state = {}
def load_model():
    model = build_model(); path = os.path.join(ART, "global_model.npz"); verified, src = None, "untrained"
    if os.path.exists(path):
        z = np.load(path); arrs = [z[f"arr_{i}"] for i in range(len(z.files))]
        h = hashlib.sha256(b"".join(a.tobytes() for a in arrs)).hexdigest()
        verified = chain.verify(h); src = "federated"
        if not verified: raise HTTPException(500, "Model hash NOT found on blockchain - possible tampering")
        model.set_weights(arrs)
    elif os.path.exists(os.path.join(ART, "centralized.weights.h5")):
        model.load_weights(os.path.join(ART, "centralized.weights.h5")); src = "centralized"
    Xtr, _, _, _, sc = get_splits()
    _state.update(model=model, sc=sc, exp=Explainer(model, Xtr), verified=verified, source=src)
    return _state

# ---- auth ----
def make_token(u): return jwt.encode({"sub": u["username"], "role": u["role"], "exp": datetime.utcnow()+timedelta(hours=8)}, SECRET)
def current_user(token: str = Depends(oauth)):
    try: return jwt.decode(token, SECRET, algorithms=["HS256"])
    except JWTError: raise HTTPException(401, "Invalid token")

class Register(BaseModel): username: str; password: str; hospital_id: str = "H1"; role: str = "doctor"
@app.post("/auth/register")
def register(r: Register):
    if db.users.find_one({"username": r.username}): raise HTTPException(400, "User exists")
    db.users.insert_one({"username": r.username, "password": pwd.hash(r.password), "hospital_id": r.hospital_id, "role": r.role})
    db.hospitals.update_one({"hospital_id": r.hospital_id}, {"$setOnInsert": {"hospital_id": r.hospital_id}}, upsert=True)
    return {"ok": True}

@app.post("/auth/login")
def login(f: OAuth2PasswordRequestForm = Depends()):
    u = db.users.find_one({"username": f.username})
    if not u or not pwd.verify(f.password, u["password"]): raise HTTPException(401, "Bad credentials")
    return {"access_token": make_token(u), "token_type": "bearer", "role": u["role"]}

# ---- patients ----
class Patient(BaseModel):
    name: str; age: int; sex: int; cp: int; trestbps: float; chol: float; thalach: float; restecg: int
def ser(d): d["id"] = str(d.pop("_id")); return d

@app.post("/patients")
def add_patient(p: Patient, u=Depends(current_user)):
    d = p.dict(); d.update(doctor=u["sub"], created=time.time())
    return {"id": str(db.patients.insert_one(d).inserted_id)}

@app.get("/patients")
def list_patients(u=Depends(current_user)):
    return [ser(d) for d in db.patients.find({"doctor": u["sub"]})]

# ---- prediction + SHAP ----
@app.post("/predict/{patient_id}")
def predict(patient_id: str, u=Depends(current_user)):
    p = db.patients.find_one({"_id": ObjectId(patient_id)})
    if not p: raise HTTPException(404, "Patient not found")
    s = _state or load_model()
    x = s["sc"].transform(np.array([[p[f] for f in FEATURES]], dtype="float32")).astype("float32")
    t = time.time(); risk = float(s["model"].predict(x, verbose=0)[0][0]); lat = (time.time()-t)*1000
    expl = s["exp"].explain(x)
    res = {"patient_id": patient_id, "risk_percent": round(risk*100, 1),
           "classification": "High Risk" if risk > .66 else "Moderate Risk" if risk > .33 else "Low Risk",
           "explanation": expl, "latency_ms": round(lat, 2), "model_source": s["source"],
           "blockchain_verified": s["verified"], "timestamp": time.time(), "doctor": u["sub"]}
    db.predictions.insert_one(dict(res)); return res

@app.get("/predictions")
def predictions(u=Depends(current_user)):
    return [ser(d) for d in db.predictions.find({"doctor": u["sub"]}).sort("timestamp", -1).limit(100)]

# ---- blockchain / models ----
@app.get("/blockchain/logs")
def logs(u=Depends(current_user)): return {"mode": chain.mode, "records": chain.records()}

@app.get("/blockchain/verify")
def verify(u=Depends(current_user)):
    path = os.path.join(ART, "global_model.npz")
    if not os.path.exists(path): raise HTTPException(404, "No global model yet. Run federated training.")
    z = np.load(path); h = hashlib.sha256(b"".join(z[f"arr_{i}"].tobytes() for i in range(len(z.files)))).hexdigest()
    return {"hash": h, "verified": chain.verify(h)}

@app.get("/analytics")
def analytics(u=Depends(current_user)):
    ps = list(db.predictions.find({"doctor": u["sub"]}))
    c = {"High Risk": 0, "Moderate Risk": 0, "Low Risk": 0}
    for p in ps: c[p["classification"]] += 1
    return {"total": len(ps), "distribution": c,
            "avg_risk": round(sum(p["risk_percent"] for p in ps)/len(ps), 1) if ps else 0,
            "avg_latency_ms": round(sum(p["latency_ms"] for p in ps)/len(ps), 2) if ps else 0}

@app.get("/health")
def health(): return {"status": "ok", "chain": chain.mode}
