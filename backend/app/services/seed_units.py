from pymongo import MongoClient
from datetime import datetime
from urllib.parse import quote_plus

username = quote_plus("pranav0909")
password = quote_plus("alertai")
uri = f"mongodb+srv://{username}:{password}@alertaicluster.gahdbz2.mongodb.net/"
client = MongoClient(uri)
db = client['alertai']

initial_units = [
    {"unit_id": "P001", "type": "police", "status": "available", "location": "Station 1", "last_updated": datetime.utcnow()},
    {"unit_id": "P002", "type": "police", "status": "available", "location": "Station 2", "last_updated": datetime.utcnow()},
    {"unit_id": "A001", "type": "ambulance", "status": "available", "location": "Hospital 1", "last_updated": datetime.utcnow()},
    {"unit_id": "F001", "type": "fire_truck", "status": "available", "location": "Fire Station 1", "last_updated": datetime.utcnow()},
]

print("Connecting to database...")
print("URI:", uri)

result = db.units.insert_many(initial_units)

print("Inserted IDs:", result.inserted_ids)
print("Done!")
