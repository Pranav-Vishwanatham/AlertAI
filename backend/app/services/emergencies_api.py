# emergencies_api.py

from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson import ObjectId
import os

# ---- CONFIG ----
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongo_db_url"
)
DB_NAME = os.getenv("DB_NAME", "alertai")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "emergency_calls")

# ---- DB CONNECTION ----
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ---- FASTAPI APP ----

router = APIRouter()

# @router.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
# )

# ---- SERIALIZATION HELPER ----

def serialize_emergency(doc):
    doc = dict(doc)
    doc['id'] = str(doc.get('_id', ''))
    doc.pop('_id', None)
    # Map Mongo fields to frontend keys
    doc['call_id'] = doc.get('call_id', '')
    doc['emergency_type'] = doc.get('emergency_type', '')
    doc['priority'] = doc.get('priority', 'LOW')
    doc['caller_name'] = doc.get('caller_name', '')
    doc['status'] = doc.get('status', 'OPEN')
    doc['location'] = doc.get('location', '')
    doc['latitude'] = doc.get('latitude', '')
    doc['longitude'] = doc.get('longitude', '')
    doc['transcript'] = doc.get('transcript', '')
    doc['ai_recommendation'] = doc.get('ai_recommendation', doc.get('recommended_actions', ''))
    # Add any other field mapping if needed
    return doc

# ---- API ENDPOINTS ----

@router.get("/emergencies")
def get_all_emergencies():
    emergencies = [serialize_emergency(doc) for doc in collection.find()]
    return {"emergencies": emergencies}

@router.get("/emergencies/by_call_id/{call_id}")
def get_emergency_by_call_id(call_id: str):
    doc = collection.find_one({"call_id": call_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Emergency not found")
    return serialize_emergency(doc)

# Example usage:
# http://localhost:8000/emergencies/by_call_id/CALL_1000

@router.get("/")
def root():
    return {"message": "AlertAI Emergencies API working!"}

# ---- RUN with: uvicorn emergencies_api:app --reload --port 8000 ----
