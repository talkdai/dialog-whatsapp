import logging
import requests
import hashlib

from typing import Any
from fastapi import APIRouter, Body, HTTPException, Query, Depends, Request
from openai import OpenAI

from .settings import (
    WHATSAPP_API_TOKEN,
    WHATSAPP_ACCOUNT_NUMBER,
    WHATSAPP_VERIFY_TOKEN,
    API_HOST,
    PROJECT_CONFIG,
    DATASET,
    OPENAI_API_KEY,
    ROUTE_SUFFIX
)
from dialog.llm.default import DialogLLM

from dialog.models.helpers import create_session
from uuid import uuid4

client = OpenAI()

router = APIRouter()

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
    "Content-Type": "application/json",
}
WHATSAPP_MESSAGES_URL = f"https://graph.facebook.com/v17.0/{WHATSAPP_ACCOUNT_NUMBER}/messages"


def _send_message(json_data):
    response = requests.post(WHATSAPP_MESSAGES_URL, json=json_data, headers=HEADERS)
    logger.info("Sending message to WhatsApp API")
    logger.info("Response from WhatsApp API - %s", response.text)
    logger.info("Response status code from WhatsApp API - %s", response.status_code)
    response.raise_for_status()
    return response.json()

def send_audio_to_whatsapp(filename, from_number):
    data = {
        "messaging_product": "whatsapp",
        "to": from_number,
        "type": "audio",
        "audio": {"link":  f"{API_HOST}/static/{filename}"},
    }
    return _send_message(data)

def send_text_to_whatsapp(text, from_number):
    data = {
        "messaging_product": "whatsapp",
        "to": from_number,
        "type": "text",
        "text": {"body": text},
    }
    return _send_message(data)

def get_media_content(media_id):
    url = f"https://graph.facebook.com/v17.0/{media_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    media_url = response.json().get("url")
    response = requests.get(media_url, headers=HEADERS)
    return response

def transcribe_audio(audio_id):
    response = get_media_content(audio_id)
    audio = response.content
    # Generate hash for file name
    file_hash = hashlib.sha256(audio).hexdigest()
    filename = f"{file_hash}.ogg"
    complete_file_path = f"/app/static/{filename}"

    with open(complete_file_path, "wb") as f:
        f.write(audio)

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=open(complete_file_path, "rb"),
        language="pt"
    )
    logger.info(f"Got transcript back from OpenAI - {transcript}")
    return transcript.text

@router.get(f"/tenant-{ROUTE_SUFFIX}")
async def whats_audio_get(request: Request):
    logging.info(request.query_params.get("hub.verify_token"))
    logging.info(WHATSAPP_VERIFY_TOKEN)
    if request.query_params.get("hub.verify_token") == WHATSAPP_VERIFY_TOKEN:
        return int(request.query_params.get("hub.challenge"))

    raise HTTPException(status_code=404)

@router.post(f"/tenant-{ROUTE_SUFFIX}")
async def whats_audio_post(body: Any = Body(None)):
    logger.info("Started")
    value = body["entry"][0]["changes"][0]["value"]
    logging.info("Body: ", body)

    try:
        from_number = value["messages"][0]["from"]
        message_type = value["messages"][0].get("type")
    except KeyError:
        return {}

    phone_number_id = value["metadata"]["phone_number_id"]
    logging.info(f"Got message for number {phone_number_id}")
    if phone_number_id != WHATSAPP_ACCOUNT_NUMBER:
        logger.info("Phone number not supported")
        return {"status": "success"}

    if message_type not in ["audio", "text"]:
        logger.info("Message type not supported")
        send_text_to_whatsapp("Ainda não consigo entender este tipo de mensagem", from_number)
        return {}

    logger.info(f"message_type - {message_type}")
    if message_type == "audio":
        audio_id = value["messages"][0]["audio"]["id"]
        message = transcribe_audio(audio_id)
    else:
        message = value["messages"][0]["text"]["body"]

    logger.info(f"Got message from {from_number} - message: {message}")

    session_id = from_number
    if DATASET:
        session_id = f"{DATASET}_{from_number}"

    create_session(identifier=session_id)

    llm = DialogLLM(
        config=PROJECT_CONFIG,
        session_id=session_id,
        dataset=DATASET,
        llm_key=OPENAI_API_KEY
    )
    logger.info(f"Project config: {PROJECT_CONFIG}")
    processed_message = llm.process(message)
    processed_message = processed_message["text"]
    logger.info("Processed message: %s", processed_message)

    # Generate the audio here
    if message_type == "audio":
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
        # Posting media to WhatsApp API
        send_audio_to_whatsapp(filename, from_number)
    else:
        send_text_to_whatsapp(processed_message, from_number)

    return {}