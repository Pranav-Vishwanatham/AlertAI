# backend/app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    speech_key: str
    speech_region: str
    openai_api_key: str
    class Config:
        env_file = ".env"

settings = Settings()