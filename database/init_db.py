"""Creates collections + indexes: python database/init_db.py"""
import os
from pymongo import MongoClient, ASCENDING
db = MongoClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))["meditrust"]
for c in ["users", "hospitals", "patients", "predictions", "blockchainlogs", "modelhistory"]:
    if c not in db.list_collection_names(): db.create_collection(c)
db.users.create_index([("username", ASCENDING)], unique=True)
db.hospitals.create_index([("hospital_id", ASCENDING)], unique=True)
db.predictions.create_index([("doctor", ASCENDING), ("timestamp", -1)])
print("Collections:", db.list_collection_names())
