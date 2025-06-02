# backend/app/services/geolocation_service.py

import requests
import logging


class GeoLocationService:
    def __init__(self):
        self.api_url = "https://nominatim.openstreetmap.org/search"

    async def enrich_with_coordinates(self, emergency_data):
        location = emergency_data.get("location")
        if not location:
            logging.warning("No location found in emergency data.")
            return emergency_data

        try:
            params = {
                "q": location,
                "format": "json",
                "limit": 1
            }
            response = requests.get(self.api_url, params=params, headers={"User-Agent": "AlertAI"})
            response.raise_for_status()
            results = response.json()

            if results:
                coords = results[0]
                emergency_data["latitude"] = float(coords["lat"])
                emergency_data["longitude"] = float(coords["lon"])
            else:
                logging.warning(f"No coordinates found for location: {location}")
        except Exception as e:
            logging.error(f"Error fetching coordinates: {e}")

        return emergency_data
