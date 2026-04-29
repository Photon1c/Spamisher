# Download the helper library from https://www.twilio.com/docs/python/install
import os
import sys

# Add src to path to find config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dotenv import load_dotenv

load_dotenv("/home/sherlockhums/apps/spamisher/.env")

from twilio.rest import Client
from config import Config

# Use parameters from Config
account_sid = Config.TWILIO_ACCOUNT_SID
auth_token = Config.TWILIO_AUTH_TOKEN
client = Client(account_sid, auth_token)

call = client.calls.create(
    twiml="<Response><Say>Ahoy, World</Say></Response>",
    to=Config.MY_PHONE_NUMBER,
    from_=Config.TWILIO_PHONE_NUMBER,
)

print(f"Call SID: {call.sid}")
print(f"To: {Config.MY_PHONE_NUMBER}")
print(f"From: {Config.TWILIO_PHONE_NUMBER}")
