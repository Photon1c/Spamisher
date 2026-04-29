# config.py
import os


class Config:
    """Configuration for Flask app, Twilio, and OpenAI APIs."""

    # Flask settings
    DEBUG = True  # True for local debugging, False for production
    TESTING = False
    EXTERNAL_URL = os.getenv("EXTERNAL_URL", "")

    # Twilio settings (loaded from environment for security)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx...")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+15558675309")
    MY_PHONE_NUMBER = os.getenv("MY_PHONE_NUMBER", "")

    # Neutts settings
    NEUTTS_PATH = os.getenv("NEUTTS_PATH", os.path.expanduser("~/tools/tts/neutts"))
    NEUTTS_VOICE = os.getenv("NEUTTS_VOICE", "jo")

    # OpenAI API Key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-...")

    # LLM Provider settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "60"))
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    # TTS Provider settings
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "twilio")
    NEUTTS_PATH = os.getenv("NEUTTS_PATH", os.path.expanduser("~/tools/tts/neutts"))
    NEUTTS_VOICE = os.getenv("NEUTTS_VOICE", "jo")
    NEUTTS_OUTPUT_DIR = os.path.join(os.getcwd(), "media")

    # Output capture
    CAPTURE_OUTPUTS = os.getenv("CAPTURE_OUTPUTS", "false").lower() == "true"

    # Other configurations
    LOG_DIR = os.path.join(os.getcwd(), "logs")
    ALLOWED_EXTENSIONS = {"wav", "mp3"}
