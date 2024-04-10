import os
import json
import tomllib
import logging

from pathlib import Path
from decouple import config
# from dialog.settings import PROJECT_CONFIG as DIALOG_PROJECT_CONFIG

file_path = os.path.abspath(__file__)
dir_path = os.path.dirname(file_path)

if "config.json" in os.listdir(dir_path):
    logging.info("Loading config file")
    config_json = json.load(open(dir_path + "/config.json"))
    WHATSAPP_VERIFY_TOKEN = config_json.get("WHATSAPP_VERIFY_TOKEN", "1234567890")
    WHATSAPP_API_TOKEN = config_json.get("WHATSAPP_API_TOKEN", "1234567890")
    WHATSAPP_ACCOUNT_NUMBER = config_json.get("WHATSAPP_ACCOUNT_NUMBER", "")
    API_HOST = config_json.get("API_HOST")
    PROJECT_CONFIG = tomllib.loads(Path(dir_path + "/" + config_json.get("PROJECT_CONFIG")).read_text())
    DATASET = config_json.get("DATASET")
    OPENAI_API_KEY = config_json.get("OPENAI_API_KEY")
    ROUTE_SUFFIX = config_json.get("ROUTE_SUFFIX")
else:
    WHATSAPP_VERIFY_TOKEN = config("WHATSAPP_VERIFY_TOKEN", "1234567890")
    WHATSAPP_API_TOKEN = config("WHATSAPP_API_TOKEN", "1234567890")
    WHATSAPP_ACCOUNT_NUMBER = config("WHATSAPP_ACCOUNT_NUMBER", "")
    API_HOST = config("API_HOST", "http://localhost:8000")
    PROJECT_CONFIG = config(
        "PROJECT_CONFIG",
        cast=lambda filename: tomllib.loads(Path(filename).read_text()),
        default={}
    )
    DATASET = config("DATASET", None)
    OPENAI_API_KEY = config("OPENAI_API_KEY", None)
    ROUTE_SUFFIX = 1