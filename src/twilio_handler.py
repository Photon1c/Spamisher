# twilio_handler.py
from twilio.twiml.voice_response import VoiceResponse
from src.openai_handler import transcribe_audio, generate_ai_reply
from src.audio_handler import find_canned_response, synthesize_speech
import os
from src.config import Config


def handle_incoming_call():
    """
    Generate TwiML to greet the caller and start recording their speech.
    Uses a stall tactic for the first interaction.
    """
    resp = VoiceResponse()
    # Scenario 2 implementation: Start with a stall tactic to catch humans or bots
    resp.say(
        "Hi, hang on one second. Can you give me a moment?",
        voice="alice",
        language="en",
    )
    # Stall buffer: provide immediate response before recording
    # Record the caller's voice. After recording, Twilio will hit the /voice/recording endpoint.
    resp.record(
        play_beep=False,  # Discreet recording
        max_length=30,
        timeout=5,
        action="/voice/recording",
    )
    return resp


def handle_recording(recording_url, caller_number=""):
    """
    Process the call recording: transcribe, classify, and decide on tarpit vs interrogation.
    """
    resp = VoiceResponse()
    if not recording_url:
        resp.say("Sorry, I didn't catch that. Goodbye.", voice="alice")
        return resp

    # Step 1: Transcribe the audio using OpenAI Whisper
    transcript_text = transcribe_audio(recording_url)

    # Step 2: Immediate Stall Audio (Play while deciding)
    # This keeps the line alive without silence
    # resp.play("/media/stall_clip.wav") # Placeholder for future canned clips

    if not transcript_text:
        # BOT DETECTED (No speech or failed transcription)
        return tarpit_path(resp)

    # Step 3: Classification logic
    from spamisher.classifier import detect_category

    category = detect_category(transcript_text)

    # Step 4: Decision Tactic
    if category in ["warranty", "crypto", "debt_collection", "phishing"]:
        # Known spam category -> Interrogation-lite
        return interrogation_path(resp, transcript_text)
    elif len(transcript_text.split()) < 3:
        # Too short -> Bot or silent human
        return tarpit_path(resp)

    # Step 5: AI Generation for complex cases
    ai_reply = generate_ai_reply(transcript_text)
    resp.say(ai_reply if ai_reply else "One moment please.", voice="alice")

    # Continue recording for loop
    resp.record(action="/voice/recording", max_length=30, timeout=5)

    log_conversation(caller_number, transcript_text, ai_reply)
    return resp


def tarpit_path(resp):
    """Waste bot/spam caller time."""
    resp.say("Please hold while I check that.", voice="alice")
    resp.pause(length=10)
    resp.say("Thank you. One more moment.", voice="alice")
    resp.pause(length=20)
    resp.say(
        "I'm sorry, I couldn't find your record. Please call back later.", voice="alice"
    )
    resp.hangup()
    return resp


def interrogation_path(resp, transcript):
    """Ask verification questions to human spammers."""
    questions = [
        "What company are you with?",
        "What is your callback number?",
        "Can you spell your full name?",
        "What account or case number is this about?",
    ]
    # Simple state machine can be added later, for now ask next question
    resp.say("Thanks. " + questions[0], voice="alice")
    resp.record(action="/voice/recording", max_length=15, timeout=3)
    return resp


def handle_recording(recording_url, caller_number=""):
    """
    Process the call recording: transcribe it, determine a response, and return TwiML with that response.
    """
    resp = VoiceResponse()
    if not recording_url:
        resp.say("Sorry, I didn't catch that. Goodbye.", voice="alice")
        return resp

    # Step 1: Transcribe the audio using OpenAI Whisper
    transcript_text = transcribe_audio(recording_url)
    if not transcript_text:
        # If transcription failed, end the call politely
        resp.say("Thank you. Goodbye.", voice="alice")
        log_conversation(
            caller_number,
            transcript_text=None,
            response_text="(no response, transcription failed)",
        )
        return resp

    # Step 2: Decide on a response (canned or AI-generated)
    audio_file = find_canned_response(transcript_text)
    if audio_file:
        # We have a relevant canned response audio file
        resp.play(audio_file)  # play the pre-recorded response
        response_text = f"[Played canned audio: {os.path.basename(audio_file)}]"
    else:
        # No canned clip fits, use AI to generate a reply text
        ai_reply = generate_ai_reply(transcript_text)
        response_text = ai_reply if ai_reply else "Thank you. Goodbye."
        # Use Twilio <Say> with a friendly voice to speak the AI reply
        resp.say(response_text, voice="man", language="en")
        # (Alternatively, use synthesize_speech() to get an audio URL and resp.play it)
    # Step 3: Log the interaction for review
    log_conversation(caller_number, transcript_text, response_text)
    return resp


def log_conversation(caller_number, transcript_text, response_text):
    """
    Append the call transcript and response to a log file for record-keeping.
    """
    from spamisher.storage import save_call_log
    from spamisher.models import CallLog
    import datetime
    import uuid

    # Save to JSONL for dashboard
    log_entry = CallLog(
        sid=str(uuid.uuid4()),  # Using UUID if SID not provided in this context
        from_number=caller_number,
        to_number=Config.TWILIO_PHONE_NUMBER,
        status="completed",
        direction="inbound",
        timestamp=datetime.datetime.now().isoformat(),
        transcript=transcript_text,
    )
    save_call_log(log_entry)

    if not os.path.isdir(Config.LOG_DIR):
        os.makedirs(Config.LOG_DIR, exist_ok=True)
    log_file = os.path.join(Config.LOG_DIR, "calls.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"Caller: {caller_number}\n")
        if transcript_text is not None:
            f.write(f"Transcript: {transcript_text}\n")
        else:
            f.write("Transcript: [Unavailable]\n")
        f.write(f"Response: {response_text}\n")
        f.write("-" * 40 + "\n")
