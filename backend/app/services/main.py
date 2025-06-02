# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
#
# from .units_api import router as units_router
# from .emergencies_api import router as emergencies_router
# from .assignment_api import router as assignment_router
#
# app = FastAPI()
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# app.include_router(units_router)
# app.include_router(emergencies_router)
# app.include_router(assignment_router)
# @app.get("/")
# def root():
#     return {"message": "AlertAI API Main App is working!"}




from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Import routers and handlers with full package path
from app.api.endpoints.twilio_webhook import router as twilio_router
from app.services.assignment_api import router as assignment_router
from app.services.emergencies_api import router as emergencies_router
from app.services.units_api import router as units_router
from app.services.emergency_handler import emergency_handler

# Set up logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the transcripts directory exists
os.makedirs("transcripts", exist_ok=True)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers for your endpoints
app.include_router(twilio_router, prefix="/api")
app.include_router(assignment_router, prefix="/api")
app.include_router(emergencies_router, prefix="/api")
app.include_router(units_router, prefix="/api")

# WebSocket for real-time streaming
@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await emergency_handler.handle_call(websocket)
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")
    except Exception as e:
        logging.error(f"Error in WebSocket connection: {str(e)}", exc_info=True)
    finally:
        logging.info("WebSocket connection closed")

@app.get("/api/analysis/{call_id}")
async def get_analysis(call_id: str):
    result = await emergency_handler.get_analysis_result(call_id)
    if result:
        return result
    raise HTTPException(status_code=404, detail="Analysis not found")

@app.get("/")
async def root():
    return {"message": "Emergency Response System API"}

# to execute run # uvicorn app.services.main:app --reload