# routes.py
from flask import Blueprint, request, make_response, jsonify, render_template
from twilio.twiml.voice_response import VoiceResponse
from twilio_handler import handle_incoming_call, handle_recording
import os

# Define a Blueprint for voice-related routes
voice_bp = Blueprint("voice", __name__)


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
    Twilio will post recording URL and other data here.
    """
    recording_url = request.form.get("RecordingUrl")
    caller_number = request.form.get("From", "Unknown")  # caller's number
    # Process the recording: transcribe and generate response TwiML
    twiml_response = handle_recording(recording_url, caller_number)
    return make_response(str(twiml_response), 200, {"Content-Type": "text/xml"})


@voice_bp.route("/voice/probe", methods=["GET", "POST"])
def voice_probe():
    """Basic probe returning simple TwiML."""
    resp = VoiceResponse()
    resp.say("Spamisher voice probe is online.", voice="alice")
    return make_response(str(resp), 200, {"Content-Type": "text/xml"})


@voice_bp.route("/voice/probe/play", methods=["GET", "POST"])
def voice_probe_play():
    """Probe with audio playback."""
    audio_url = os.environ.get("SPAMISHER_TEST_AUDIO_URL")
    if not audio_url:
        resp = VoiceResponse()
        resp.say("Audio URL not configured.", voice="alice")
        return make_response(str(resp), 200, {"Content-Type": "text/xml"})
    resp = VoiceResponse()
    resp.play(audio_url)
    return make_response(str(resp), 200, {"Content-Type": "text/xml"})


@voice_bp.route("/voice/probe/gather", methods=["GET", "POST"])
def voice_probe_gather():
    """Probe with Gather for speech/dtmf input."""
    resp = VoiceResponse()
    with resp.gather(input="speech dtmf", timeout=5, action="/voice/probe") as gather:
        gather.say("Please speak or press digits.")
    resp.say("No input received.", voice="alice")
    return make_response(str(resp), 200, {"Content-Type": "text/xml"})


@voice_bp.route("/", methods=["GET"])
def index():
    """Dashboard index page."""
    return render_template("index.html")


@voice_bp.route("/voice/tts", methods=["POST"])
def voice_tts():
    """Generate TwiML with TTS text."""
    text = request.form.get("text", "Hello.")
    voice = request.form.get("voice", "alice")
    resp = VoiceResponse()
    resp.say(text, voice=voice)
    return make_response(str(resp), 200, {"Content-Type": "text/xml"})


@voice_bp.route("/voice/tts_clone", methods=["POST"])
def voice_tts_clone():
    """Generate TwiML with Neutts voice cloning - plays in browser."""
    text = request.form.get("text", "Hello.")
    voice = request.form.get("voice", "jo")

    if not text:
        return jsonify({"error": "No text provided"})

    from model_config import ModelConfig
    from flask import request as flask_request

    tts_provider = ModelConfig.get_tts_provider()

    twiml = tts_provider.synthesize(text, voice)

    if "/media/" in twiml:
        import re

        match = re.search(r'/media/[^"]+', twiml)
        audio_filename = match.group(0).replace("/media/", "") if match else None
        if audio_filename:
            full_url = f"{flask_request.host_url.rstrip('/')}/media/{audio_filename}"
            return jsonify({"audio_url": full_url, "text": text})
        return jsonify({"twiml": twiml, "text": text})
    else:
        return jsonify({"twiml": twiml, "text": text})


@voice_bp.route("/voice/tts/preview", methods=["POST"])
def voice_tts_preview():
    """Preview TTS - returns TwiML (Twilio handles audio)."""
    text = request.form.get("text", "Hello.")
    voice = request.form.get("voice", "alice")
    resp = VoiceResponse()
    resp.say(text, voice=voice)
    return jsonify({"twiml": str(resp)})


@voice_bp.route("/voice/ai_reply", methods=["POST"])
def voice_ai_reply():
    """Test AI reply generation."""
    transcript = request.form.get("transcript", "")
    if not transcript:
        return make_response(
            "<Response><Say>No transcript provided.</Say></Response>",
            200,
            {"Content-Type": "text/xml"},
        )
    from openai_handler import generate_ai_reply

    reply = generate_ai_reply(transcript)
    resp = VoiceResponse()
    resp.say(reply, voice="alice")
    return make_response(str(resp), 200, {"Content-Type": "text/xml"})


@voice_bp.route("/voice/transcribe", methods=["POST"])
def voice_transcribe():
    """Test transcription."""
    audio_url = request.form.get("audio_url", "")
    if not audio_url:
        return make_response(
            "<Response><Say>No audio URL provided.</Say></Response>",
            200,
            {"Content-Type": "text/xml"},
        )
    from openai_handler import transcribe_audio

    transcript = transcribe_audio(audio_url)
    resp = VoiceResponse()
    if transcript:
        resp.say(f"Transcribed: {transcript}", voice="alice")
    else:
        resp.say("Transcription failed.", voice="alice")
    return make_response(str(resp), 200, {"Content-Type": "text/xml"})


@voice_bp.route("/voice/status", methods=["GET"])
def voice_status():
    """System status check."""
    from config import Config
    import os

    audio_url = os.environ.get("SPAMISHER_TEST_AUDIO_URL")
    return jsonify(
        {
            "twilio": bool(
                Config.TWILIO_ACCOUNT_SID
                and Config.TWILIO_ACCOUNT_SID != "ACxxxxxxxx..."
            ),
            "openai": bool(
                Config.OPENAI_API_KEY and not Config.OPENAI_API_KEY.startswith("sk-...")
            ),
            "audio_url": bool(audio_url),
        }
    )


@voice_bp.route("/voice/ai_clone", methods=["POST"])
def voice_ai_clone():
    """Generate AI reply with Neutts voice cloning - plays in browser."""
    transcript = request.form.get("transcript", "")
    voice = request.form.get("voice", "jo")

    if not transcript:
        return jsonify({"error": "No transcript provided"})

    # Generate AI reply first
    from openai_handler import generate_ai_reply

    ai_text = generate_ai_reply(transcript)

    if not ai_text:
        return jsonify({"error": "Failed to generate AI reply"})

    # Use model config to generate cloned audio
    from model_config import ModelConfig
    from flask import request as flask_request

    tts_provider = ModelConfig.get_tts_provider()

    twiml = tts_provider.synthesize(ai_text, voice)

    # Check if we got an audio URL or need to extract it
    if "/media/" in twiml:
        import re

        match = re.search(r'/media/[^"]+', twiml)
        audio_filename = match.group(0).replace("/media/", "") if match else None
        if audio_filename:
            full_url = f"{flask_request.host_url.rstrip('/')}/media/{audio_filename}"
            return jsonify({"audio_url": full_url, "text": ai_text})
        return jsonify({"twiml": twiml, "text": ai_text})
    else:
        return jsonify({"twiml": twiml, "text": ai_text})


@voice_bp.route("/voice/call_me", methods=["POST"])
def voice_call_me():
    """Make an outbound call to test TTS - calls the configured Twilio number."""
    from config import Config

    text = request.form.get("text", "Hello, this is a test from Spamisher.")
    voice = request.form.get("voice", "alice")

    # Use MY_PHONE_NUMBER from config, fallback to TWILIO_PHONE_NUMBER
    to_number = getattr(Config, "MY_PHONE_NUMBER", None) or Config.TWILIO_PHONE_NUMBER

    try:
        from twilio.rest import Client

        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        resp = VoiceResponse()
        resp.say(text, voice=voice)

        call = client.calls.create(
            twiml=str(resp), to=to_number, from_=Config.TWILIO_PHONE_NUMBER
        )
        return jsonify({"status": "calling", "call_sid": call.sid, "to": to_number})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})
