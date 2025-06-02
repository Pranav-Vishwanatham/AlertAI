from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime

router = APIRouter()

# --- Database connection ---
MONGODB_URI = "mongo_db_url"
DATABASE_NAME = "alertai"

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

class AssignUnitRequest(BaseModel):
    call_id: str
    unit_type: str

@router.post("/assign_unit")
def assign_unit(req: AssignUnitRequest):
    call_id = req.call_id
    unit_type = req.unit_type

    # Find the first available unit of the requested type
    unit = db.units.find_one({"type": unit_type, "status": "available"})
    if not unit:
        raise HTTPException(status_code=404, detail=f"No available unit of type {unit_type}")

    unit_id = unit["unit_id"]

    # 1. Set the unit status to "ASSIGNED"
    unit_result = db.units.update_one(
        {"unit_id": unit_id},
        {"$set": {"status": "ASSIGNED", "last_updated": datetime.utcnow()}}
    )
    if unit_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Unit not found")

    # 2. Assign the unit to the emergency and update its status to ASSIGNED
    # Store as an object with both id and type!
    emer_result = db.emergency_calls.update_one(
        {"call_id": call_id},
        {"$addToSet": {"assigned_unit": {"unit_id": unit_id, "unit_type": unit_type}},
         "$set": {"status": "ASSIGNED"}}
    )
    if emer_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Emergency not found")

    return {
        "success": True,
        "call_id": call_id,
        "assigned_unit": unit_id,
        "unit_type": unit_type
    }
