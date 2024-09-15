# backend/app/services/azure_speech_service.py

import azure.cognitiveservices.speech as speechsdk
from app.core.config import settings
import base64
import audioop
import asyncio

class AzureSpeechService:
    def __init__(self):
        self.speech_config = speechsdk.SpeechConfig(subscription=settings.speech_key, region=settings.speech_region)
        self.speech_config.speech_recognition_language = "en-US"

    async def transcribe_stream(self, websocket):
        audio_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)

        async def send_result(result):
            await websocket.send_text(result)

        def recognizing_callback(event):
            """Callback to handle interim speech recognition results"""
            if event.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                print(f"{event.result.text}")
                asyncio.create_task(send_result(event.result.text))

        # Connect callback to the recognizing event
        speech_recognizer.recognizing.connect(recognizing_callback)
        
        # Start continuous speech recognition
        speech_recognizer.start_continuous_recognition()

        try:
            async for message in websocket.iter_json():
                if message['event'] == 'media':
                    audio = base64.b64decode(message['media']['payload'])
                    audio = audioop.ulaw2lin(audio, 2)
                    audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
                    audio_stream.write(audio)
                elif message['event'] == 'stop':
                    speech_recognizer.stop_continuous_recognition()
                    audio_stream.close()
                    await websocket.send_text("Transcription completed.")
                    break
        except Exception as e:
            print(f"Error in transcribe_stream: {str(e)}")
        finally:
            speech_recognizer.stop_continuous_recognition()
            audio_stream.close()

azure_speech_service = AzureSpeechService()