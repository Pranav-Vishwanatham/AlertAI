# backend/app/services/mongodb_service.py

from pymongo import MongoClient
from app.core.config import settings
import logging
import asyncio
from datetime import datetime

class MongoDBService:
    def __init__(self):
        self.client = MongoClient(settings.mongodb_url)
        self.db = self.client[settings.mongodb_db_name]
        self.collection = self.db[settings.mongodb_collection_name]

    async def insert_emergency_data(self, emergency_data, transcript, call_id):
        try:
            document = {
                "call_id": call_id,
                "emergency_type": emergency_data.get("emergency_type"),
                "priority": emergency_data.get("priority"),
                "location": emergency_data.get("location"),
                "caller_name": emergency_data.get("caller_name"),
                "critical_info": emergency_data.get("critical_info"),
                "priority_explanation": emergency_data.get("priority_explanation"),
                "recommended_actions": emergency_data.get("recommended_actions"),
                "transcript": transcript,
                "time": datetime.utcnow(),
                "latitude": emergency_data.get("latitude"),
                "longitude": emergency_data.get("longitude"),
                "status": "unassigned"
            }
            # Use run_in_executor to run the synchronous insert operation asynchronously
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.collection.insert_one, document
            )
            logging.info(f"Emergency data inserted with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            logging.error(f"Error inserting emergency data into MongoDB: {str(e)}")
            return None

mongodb_service = MongoDBService()