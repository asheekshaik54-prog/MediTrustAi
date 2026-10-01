# MediTrust AI - Secure Federated Edge AI Healthcare Platform using Blockchain

Heart-disease prediction with Federated Learning (Flower, 3 hospitals), SHA-256 model hashes on Ethereum (Ganache),
SHAP explainability, FastAPI + MongoDB backend, React + Tailwind dashboard, Docker deployment.

## Quick start (local)
```bash
pip install -r requirements.txt
# Optional: put UCI heart.csv in data/ (cols: age,sex,cp,trestbps,chol,thalach,restecg,target). Otherwise synthetic data is used.
python -m ai_model.train                 # centralised baseline + scaler
docker compose up -d mongo ganache       # DB + blockchain
python -m blockchain.deploy              # deploy ModelRegistry.sol (optional; falls back to local hash-chained ledger)
python database/init_db.py
python -m federated.simulate             # 3 hospitals, 5 rounds -> artifacts/global_model.npz + chain records
uvicorn backend.main:app --reload        # API on :8000 (docs at /docs)
cd frontend && npm install && npm run dev   # UI on :5173
```
## Full Docker
`docker compose up --build` (app) and `docker compose --profile fl up` (federated server + 3 hospital nodes).
Run `python -m ai_model.train` first so the scaler exists in `artifacts/`.

## Flow (matches report section 7)
Doctor registers patient -> features entered -> scaled -> hospitals train locally -> Flower FedAvg aggregates ->
SHA-256 of global weights stored on blockchain -> backend verifies hash before loading model -> prediction + SHAP -> dashboard/history.

## Notes
- Evaluation metrics (accuracy, precision, recall, F1, ROC-AUC, latency): `artifacts/centralized_metrics.json`;
  federated accuracy is printed per round by the server.
- Set `JWT_SECRET` in production. Not a certified medical device.
- Tested: Python syntax of all modules. Full runtime not executed here (no network to install TensorFlow/Flower).
