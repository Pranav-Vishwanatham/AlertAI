# backend/app/services/openai_service.py

from openai import AsyncOpenAI
from app.core.config import settings
import logging
import json

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def analyze_emergency(self, transcript_file):
        try:
            with open(transcript_file, 'r') as file:
                transcript = file.read()

            prompt = f"""
            Analyze the following emergency call transcript and extract key information.
            Provide the following details:
            1. Emergency type
            2. Priority level (LOW, MEDIUM, HIGH)
            3. Location (if mentioned)
            4. Caller's name (if mentioned)
            5. Any other critical information (Summarize this into bullets)
            6. Recommended Actions

            Also, provide a brief explanation for the priority level.
            Also, provide recommended actions that can be taken provided the information.

            Transcript: {transcript}

            Format the response as JSON:
            {{
                "emergency_type": "",
                "priority": "LOW/MEDIUM/HIGH",
                "location": "",
                "caller_name": "",
                "critical_info": "",
                "priority_explanation": ""
                "recommended_actions": ""
            }}
            """

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an emergency response AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            content = response.choices[0].message.content
            # logging.debug(f"OpenAI response: {content}")
            return json.loads(content)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from OpenAI response: {e}")
            logging.error(f"Raw response content: {content}")
            return None
        except Exception as e:
            logging.error(f"Error in analyze_emergency: {str(e)}")
            return None

openai_service = OpenAIService()