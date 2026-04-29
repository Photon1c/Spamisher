#!/usr/bin/env python
"""Test script to verify Twilio outgoing calls."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dotenv import load_dotenv

load_dotenv("/home/sherlockhums/apps/spamisher/.env")

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from config import Config


def main():
    print("=" * 50)
    print("Twilio Outbound Call Test")
    print("=" * 50)

    print(f"\nConfiguration:")
    print(f"  TWILIO_ACCOUNT_SID: {Config.TWILIO_ACCOUNT_SID[:20]}...")
    print(f"  TWILIO_AUTH_TOKEN: {Config.TWILIO_AUTH_TOKEN[:10]}...")
    print(f"  TWILIO_PHONE_NUMBER: {Config.TWILIO_PHONE_NUMBER}")
    print(f"  MY_PHONE_NUMBER: {Config.MY_PHONE_NUMBER}")

    text = input(
        "\nEnter message to say [default: Hello, this is Spamisher calling.]: "
    )
    if not text.strip():
        text = "Hello, this is Spamisher calling."

    target = input(f"Enter target number [{Config.MY_PHONE_NUMBER}]: ")
    if not target.strip():
        target = Config.MY_PHONE_NUMBER

    print(f"\nCreating call to {target}...")

    client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    resp = VoiceResponse()
    resp.say(text, voice="alice")

    twiml = str(resp)
    print(f"TwiML: {twiml}")

    try:
        call = client.calls.create(
            twiml=twiml, to=target, from_=Config.TWILIO_PHONE_NUMBER
        )
        print(f"\nCall created!")
        print(f"  SID: {call.sid}")
        print(f"  Status: {call.status}")
        print(f"\nCheck your phone - you should receive the call.")

        # Check call status after a few seconds
        input("\nPress Enter to check call status...")
        updated = client.calls(call.sid).fetch()
        print(f"  Status: {updated.status}")
        print(f"  Duration: {updated.duration} seconds")

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
