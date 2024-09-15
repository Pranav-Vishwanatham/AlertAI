# backend/app/api/endpoints/twilio_webhook.py

from fastapi import APIRouter, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Start
import logging

router = APIRouter()
logging.basicConfig(level=logging.DEBUG)

async def handle_call(request: Request):
    logging.info("Received call request")
    try:
        form_data = await request.form()
        logging.debug(f"Form data: {form_data}")

        response = VoiceResponse()
        start = Start()
        # Ensure this URL matches the WebSocket route in main.py
        start.stream(url=f'wss://{request.headers["host"]}/ws/stream')
        response.append(start)
        response.say('Please describe your emergency')
        response.pause(length=60)  # Keep the call active for 60 seconds

        logging.info(f'Incoming call from {form_data.get("From", "Unknown")}')
        logging.debug(f"TwiML response: {response}")
        return Response(content=str(response), media_type="application/xml")
    except Exception as e:
        logging.error(f"Error in call handler: {str(e)}", exc_info=True)
        return Response(content="Internal server error", status_code=500)

@router.post("/webhook")
async def webhook(request: Request):
    return await handle_call(request)

@router.post("/call")
async def call(request: Request):
    return await handle_call(request)

@router.get("/test")
async def test():
    return {"message": "Webhook endpoint is accessible"}