# backend/app/main.py

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.twilio_webhook import router as twilio_router
from app.services.azure_speech_service import azure_speech_service

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router for the Twilio webhook
app.include_router(twilio_router, prefix="/api")

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await azure_speech_service.transcribe_stream(websocket)
    except Exception as e:
        print(f"Error in WebSocket connection: {str(e)}")
    finally:
        await websocket.close()

@app.get("/")
async def root():
    return {"message": "Emergency Response System API"}