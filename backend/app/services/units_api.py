# units_api.py

from fastapi import FastAPI, HTTPException, Body
from pymongo import MongoClient
from datetime import datetime

from fastapi import APIRouter
from pymongo import MongoClient

MONGODB_URI = "mongo_db_url"
DATABASE_NAME = "alertai"

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
router = APIRouter()


# Generic get count endpoint
@router.get("/units/count")
def get_unit_count(type: str, status: str = "available"):
    count = db.units.count_documents({"type": type, "status": status})
    return {"count": count}

# Get all units by type
@router.get("/units/")
def get_units(type: str):
    units = list(db.units.find({"type": type}, {"_id": 0}))
    return {"units": units}

# Update unit status
@router.post("/units/update")
def update_unit_status(unit_id: str = Body(...), status: str = Body(...)):
    result = db.units.update_one(
        {"unit_id": unit_id},
        {"$set": {"status": status, "last_updated": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")
    return {"success": True, "unit_id": unit_id, "new_status": status}

# Add a new unit (admin use)
@router.post("/units/add")
def add_unit(unit_id: str = Body(...), type: str = Body(...), location: str = Body(...)):
    db.units.insert_one({
        "unit_id": unit_id,
        "type": type,
        "status": "available",
        "location": location,
        "last_updated": datetime.utcnow()
    })
    return {"success": True, "unit_id": unit_id}
