# backend/app/services/twilio_service.py

from twilio.request_validator import RequestValidator
from fastapi import Request
from app.core.config import settings
import logging

async def validate_twilio_request(request: Request) -> bool:
    validator = RequestValidator(settings.twilio_auth_token)

    # Get the URL of the request
    url = str(request.url)
    # logging.debug(f"Request URL: {url}")

    # Get the POST data
    form_data = await request.form()
    post_data = {key: value for key, value in form_data.items()}
    # logging.debug(f"POST data: {post_data}")

    # Get the X-Twilio-Signature header
    signature = request.headers.get('X-Twilio-Signature', '')
    # logging.debug(f"Twilio Signature: {signature}")

    # Validate the request
    is_valid = validator.validate(url, post_data, signature)
    # logging.debug(f"Request validation result: {is_valid}")

    return is_valid