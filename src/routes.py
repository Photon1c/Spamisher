# routes.py
from flask import Blueprint, request, make_response, jsonify, render_template
from twilio.twiml.voice_response import VoiceResponse
from src.twilio_handler import handle_incoming_call, handle_recording
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
    from src.openai_handler import generate_ai_reply

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
    from src.openai_handler import transcribe_audio

    transcript = transcribe_audio(audio_url)
    resp = VoiceResponse()
    if transcript:
        resp.say(f"Transcribed: {transcript}", voice="alice")
    else:
        resp.say("Transcription failed.", voice="alice")
    return make_response(str(resp), 200, {"Content-Type": "text/xml"})


@voice_bp.route("/voice/logs", methods=["GET"])
def voice_logs():
    """Fetch call history from Twilio and local logs."""
    from config import Config
    from twilio.rest import Client
    from spamisher.storage import load_call_logs

    try:
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        # Fetch last 20 calls from Twilio
        twilio_calls = client.calls.list(limit=20)

        history = []
        for c in twilio_calls:
            history.append(
                {
                    "sid": c.sid,
                    "from": c._from,
                    "to": c.to,
                    "status": c.status,
                    "direction": c.direction,
                    "start_time": c.start_time.isoformat() if c.start_time else None,
                    "duration": c.duration,
                }
            )

        local_logs = load_call_logs()

        return jsonify({"twilio_history": history, "local_logs": local_logs})
    except Exception as e:
        return jsonify({"error": str(e)})


@voice_bp.route("/voice/status", methods=["GET"])
def voice_status():
    """System status check."""
    from src.config import Config
    import os

    audio_url = os.environ.get("SPAMISHER_TEST_AUDIO_URL")

    # Twilio: configured if SID is set and not the placeholder
    twilio_configured = bool(
        Config.TWILIO_ACCOUNT_SID and Config.TWILIO_ACCOUNT_SID != "ACxxxxxxxx..."
    )

    # OpenAI: configured if key is set and looks like a valid key (starts with sk-)
    openai_configured = bool(
        Config.OPENAI_API_KEY
        and Config.OPENAI_API_KEY.startswith("sk-")
        and Config.OPENAI_API_KEY != "sk-..."
    )

    return jsonify(
        {
            "twilio": twilio_configured,
            "openai": openai_configured,
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
    from src.openai_handler import generate_ai_reply

    ai_text = generate_ai_reply(transcript)

    if not ai_text:
        return jsonify({"error": "Failed to generate AI reply"})

    # Use model config to generate cloned audio
    from src.model_config import ModelConfig
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
    from src.config import Config

    text = request.form.get("text", "Hello, this is a test from Spamisher.")
    voice = request.form.get("voice", "alice")

    # Debug: check what values we have
    print(f"[DEBUG] TWILIO_ACCOUNT_SID: {Config.TWILIO_ACCOUNT_SID[:20]}...")
    print(f"[DEBUG] MY_PHONE_NUMBER: {Config.MY_PHONE_NUMBER}")
    print(f"[DEBUG] TWILIO_PHONE_NUMBER: {Config.TWILIO_PHONE_NUMBER}")

    # Use MY_PHONE_NUMBER from config, fallback to TWILIO_PHONE_NUMBER
    to_number = Config.MY_PHONE_NUMBER or Config.TWILIO_PHONE_NUMBER

    try:
        from twilio.rest import Client
        from src.model_config import ModelConfig

        # Use the TTS provider to generate the TwiML
        # This will use Neutts if configured, or fallback to Twilio TTS
        tts_provider = ModelConfig.get_tts_provider()

        # DEBUG: Log exact text being sent to synthesis
        print(f"[DEBUG] Synthesizing text: {text[:50]}...")
        twiml_str = tts_provider.synthesize(text, voice)

        # If Neutts was used, twiml_str will contain <Play>/media/...</Play>
        # If Twilio fallback was used, it will contain <Say>...</Say>

        # Extract audio URL for dashboard replay if available
        audio_url = None
        if "<Play>" in twiml_str:
            import re

            match = re.search(r"<Play>(.*?)</Play>", twiml_str)
            if match:
                audio_url = match.group(1)

        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

        print(f"[DEBUG] TwiML: {twiml_str}")

        call = client.calls.create(
            twiml=twiml_str,
            to=to_number,
            from_=Config.TWILIO_PHONE_NUMBER,
            caller_id=Config.TWILIO_PHONE_NUMBER,
        )

        # Debug: Get call status
        call_status = client.calls(call.sid).fetch()
        print(f"[DEBUG] Call SID: {call.sid}, Status: {call_status.status}")

        return jsonify(
            {
                "status": "calling",
                "call_sid": call.sid,
                "to": to_number,
                "call_status": call_status.status,
                "audio_url": audio_url,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})
