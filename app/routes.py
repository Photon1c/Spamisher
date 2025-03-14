# routes.py
from flask import Blueprint, request, make_response
from twilio.twiml.voice_response import VoiceResponse
from twilio_handler import handle_incoming_call, handle_recording

# Define a Blueprint for voice-related routes
voice_bp = Blueprint('voice', __name__)

@voice_bp.route("/voice", methods=["POST"])
def voice_webhook():
    """
    Webhook for incoming Twilio calls (Twilio will POST here when a call comes in).
    This responds immediately with TwiML instructions to handle the call.
    """
    # Use Twilio handler to get an initial TwiML response (e.g., greet and record)
    twiml_response = handle_incoming_call()
    # Return the TwiML XML as a Flask response with the correct content type
    return make_response(str(twiml_response), 200, {"Content-Type": "text/xml"})

@voice_bp.route("/voice/recording", methods=["POST"])
def voice_recording():
    """
    Callback endpoint for Twilio when a recording is finished.
    Twilio will POST recording URL and other data here.
    """
    recording_url = request.form.get("RecordingUrl")
    caller_number = request.form.get("From", "Unknown")  # caller's number
    # Process the recording: transcribe and generate response TwiML
    twiml_response = handle_recording(recording_url, caller_number)
    return make_response(str(twiml_response), 200, {"Content-Type": "text/xml"})
