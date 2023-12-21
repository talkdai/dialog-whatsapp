import requests
import logging

from typing import Any
from llm import get_llm_class
from fastapi import APIRouter, Body, HTTPException

from settings import (
    WHATSAPP_VERIFY_TOKEN,
    WHATSAPP_API_TOKEN,
    WHATSAPP_ACCOUNT_NUMBER,
    PROJECT_CONFIG
)

from models.helpers import create_session
from webhooks.responses import whatsapp_get_response

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/whats-audio")
async def whats_audio_get(request):
    content = await whatsapp_get_response(request)
    return content

@router.post("/whats-audio")
async def whats_audio_post(request, body: Any = Body(None)):
    value = body["entry"][0]["changes"][0]["value"]
    try:
        message = value["messages"][0]["text"]["body"]
    except KeyError:
        raise HTTPException(status_code=200)

    from_number = value["messages"][0]["from"]
    logger.info(value)
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_ACCOUNT_NUMBER}/messages"

    create_session(identifier=from_number)

    LLM = get_llm_class()
    llm = LLM(config=PROJECT_CONFIG, session_id=from_number)
    processed_message = llm.process(message)
    processed_message = processed_message["text"]
    logger.info("Processed message: %s", processed_message)
    # Generate the audio here
    # data = {
    #     "messaging_product": "whatsapp",
    #     "to": from_number,
    #     "type": "text",
    #     "text": {"body": processed_message},
    # }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code not in [200, 201]:
        logger.info(f"Failed request: {response.text}")

    return response.json()