# config.py
import os

class Config:
    """Configuration for Flask app, Twilio, and OpenAI APIs."""
    # Flask settings
    DEBUG = True  # True for local debugging, False for production
    TESTING = False

    # Twilio settings (loaded from environment for security)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'ACxxxxxxxx...')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+15558675309')  # Your Twilio number

    # OpenAI API Key
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-...')  # set this in your environment!

    # Other configurations
    LOG_DIR = os.path.join(os.getcwd(), 'logs')
    ALLOWED_EXTENSIONS = {'wav', 'mp3'}  # audio file types for recordings
    # (Add more settings as needed, e.g., DB connection strings for future use)
