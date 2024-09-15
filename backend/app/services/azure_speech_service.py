# backend/app/services/azure_speech_service.py

import azure.cognitiveservices.speech as speechsdk
from app.core.config import settings
import base64
import audioop
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import os

class AzureSpeechService:
    def __init__(self):
        self.speech_config = speechsdk.SpeechConfig(subscription=settings.speech_key, region=settings.speech_region)
        self.speech_config.speech_recognition_language = "en-US"
        self.executor = ThreadPoolExecutor(max_workers=1)

    async def transcribe_stream(self, audio_queue, result_queue, transcript_file):
        logging.info("Starting new transcription stream")
        audio_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)

        loop = asyncio.get_running_loop()

        def recognized_callback(event):
            if event.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = event.result.text
                asyncio.run_coroutine_threadsafe(self.write_to_file(transcript_file, text), loop)
                asyncio.run_coroutine_threadsafe(result_queue.put(text), loop)

        speech_recognizer.recognized.connect(recognized_callback)

        # Start recognition
        await loop.run_in_executor(self.executor, speech_recognizer.start_continuous_recognition)

        try:
            while True:
                audio_chunk = await audio_queue.get()
                if audio_chunk is None:  # None is our signal to stop
                    break
                audio = base64.b64decode(audio_chunk)
                audio = audioop.ulaw2lin(audio, 2)
                audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
                audio_stream.write(audio)
        finally:
            # Stop recognition
            await loop.run_in_executor(self.executor, speech_recognizer.stop_continuous_recognition)
            audio_stream.close()
            logging.info("Transcription stream closed")

        # Signal that transcription is complete
        await result_queue.put(None)

    async def write_to_file(self, file_path, text):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'a') as file:
            file.write(text + " ")
        logging.info(f"Appended to transcript: {text}")

azure_speech_service = AzureSpeechService()