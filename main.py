import logging
import requests
import hashlib

from typing import Any
from dialog.llm import get_llm_class
from fastapi import APIRouter, Body, HTTPException, Query, Depends, Request
from openai import OpenAI

from .settings import (
    WHATSAPP_VERIFY_TOKEN,
    WHATSAPP_API_TOKEN,
    WHATSAPP_ACCOUNT_NUMBER,
)
from dialog.settings import PROJECT_CONFIG

from dialog.models.helpers import create_session
from plugins.whats_audio.responses import whatsapp_get_response
from uuid import uuid4


client = OpenAI()

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/whats-audio")
async def whats_audio_get(request: Request):
    content = await whatsapp_get_response(request)
    return content

@router.post("/whats-audio")
async def whats_audio_post(body: Any = Body(None)):
    logger.info("Started")
    value = body["entry"][0]["changes"][0]["value"]
    try:
        message = value["messages"][0]["text"]["body"]
    except KeyError:
        raise HTTPException(status_code=200)

    from_number = value["messages"][0]["from"]
    logger.info(f"Got message from {from_number} - message: {message}")
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
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=processed_message,
        response_format="mp3"
    )
    # generate hash for file name
    file_hash = uuid4().hex
    filename = f"{file_hash}.mp3"
    response.stream_to_file(f"/app/static/{filename}")
    # Save response to a memory file
    logger.info("Got audio back from OpenAI")

    data = {
        "messaging_product": "whatsapp",
        "to": from_number,
        "type": "audio",
        "audio": {"link":  "https://api.talkd.ai/static/" + filename},
    }
    response = requests.post(url, json=data, headers=headers)

    # Posting media to WhatsApp API
    logger.info(f"Posted audio to WhatsApp API - {response.request.url} - {response.status_code} - {response.text}")
    response.raise_for_status()

    return {}