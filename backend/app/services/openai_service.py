# backend/app/services/openai_service.py

import openai
from app.core.config import settings

class OpenAIService:
    def __init__(self):
        openai.api_key = settings.openai_api_key

    async def categorize_emergency(self, transcript):
        prompt = f"""
        Based on the following emergency call transcript, categorize the priority as LOW, MEDIUM, or HIGH. 
        Also provide a brief explanation for the categorization.

        Transcript: {transcript}

        Priority levels:
        LOW: Non-life-threatening situations that don't require immediate attention.
        MEDIUM: Situations that require timely attention but are not immediately life-threatening.
        HIGH: Life-threatening emergencies that require immediate response.

        Format the response as JSON:
        {{
            "priority": "LOW/MEDIUM/HIGH",
            "explanation": "Brief explanation for the categorization"
        }}
        """

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an emergency response AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            return response.choices[0].message['content']
        except Exception as e:
            print(f"Error in categorize_emergency: {str(e)}")
            return None

openai_service = OpenAIService()