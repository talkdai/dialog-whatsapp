from decouple import config

WHATSAPP_VERIFY_TOKEN = config("WHATSAPP_VERIFY_TOKEN", "1234567890")
WHATSAPP_API_TOKEN = config("WHATSAPP_API_TOKEN", "1234567890")
WHATSAPP_ACCOUNT_NUMBER = config("WHATSAPP_ACCOUNT_NUMBER", "")