# backend/app/services/emergency_handler.py

from app.services.azure_speech_service import azure_speech_service
from app.services.openai_service import openai_service
from app.services.mongodb_service import mongodb_service
from app.services.geolocation_service import geolocation_service
import asyncio
import logging
import os
from datetime import datetime
from starlette.websockets import WebSocketDisconnect

class EmergencyHandler:
    def __init__(self):
        self.transcript_file = None
        self.analysis_results = {}

    async def handle_call(self, websocket):
        call_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_queue = asyncio.Queue()
        result_queue = asyncio.Queue()

        self.transcript_file = f"transcripts/transcript_{call_id}.txt"
        os.makedirs(os.path.dirname(self.transcript_file), exist_ok=True)

        transcription_task = asyncio.create_task(
            azure_speech_service.transcribe_stream(audio_queue, result_queue, self.transcript_file)
        )

        processing_task = asyncio.create_task(self.process_results(websocket, result_queue))

        try:
            async for message in websocket.iter_json():
                if message['event'] == 'media':
                    await audio_queue.put(message['media']['payload'])
                elif message['event'] == 'stop':
                    await audio_queue.put(None)  # Signal to stop transcription
                    break

            await transcription_task
            await processing_task

            # Analyze the emergency
            emergency_data = await openai_service.analyze_emergency(self.transcript_file)
            if emergency_data:
                self.analysis_results[call_id] = emergency_data
                
                # Read the transcript
                with open(self.transcript_file, 'r') as file:
                    transcript = file.read()
                # Add coordinates using the new geolocation service
                emergency_data = await geolocation_service.enrich_with_coordinates(emergency_data)
                # Insert data into MongoDB
                mongo_id = await mongodb_service.insert_emergency_data(emergency_data, transcript, call_id)
                if mongo_id:
                    logging.info(f"Emergency data inserted into MongoDB with ID: {mongo_id}")
                    mongo_id_str = str(mongo_id)
                else:
                    logging.error("Failed to insert emergency data into MongoDB")
                    mongo_id_str = "insert_failed"

                try:
                    await websocket.send_json({
                        "type": "analysis", 
                        "data": emergency_data, 
                        "call_id": call_id,
                        "mongo_id": mongo_id_str
                    })
                    logging.info(f"Emergency analysis sent for call {call_id}")
                except WebSocketDisconnect:
                    logging.warning(f"WebSocket disconnected before sending analysis for call {call_id}")
            else:
                logging.error(f"Failed to analyze emergency for call {call_id}")

            try:
                await websocket.send_json({"type": "status", "message": "Call handling completed", "call_id": call_id})
            except WebSocketDisconnect:
                logging.warning(f"WebSocket disconnected before sending completion status for call {call_id}")

        except WebSocketDisconnect:
            logging.warning(f"WebSocket disconnected during call handling for call {call_id}")
        except Exception as e:
            logging.error(f"Error in handle_call for call {call_id}: {str(e)}", exc_info=True)
        finally:
            if not transcription_task.done():
                transcription_task.cancel()
            try:
                await transcription_task
            except asyncio.CancelledError:
                pass

    async def process_results(self, websocket, result_queue):
        while True:
            try:
                result = await result_queue.get()
                if result is None:  # Signal that transcription is complete
                    break
                try:
                    await websocket.send_json({"type": "transcription", "text": result})
                except WebSocketDisconnect:
                    logging.warning("WebSocket disconnected while sending transcription")
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error processing result: {str(e)}", exc_info=True)
                break
        logging.info(f"Transcription saved to {self.transcript_file}")

    async def get_analysis_result(self, call_id):
        return self.analysis_results.get(call_id)

emergency_handler = EmergencyHandler()