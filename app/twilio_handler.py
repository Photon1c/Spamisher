# twilio_handler.py
from twilio.twiml.voice_response import VoiceResponse
from openai_handler import transcribe_audio, generate_ai_reply
from audio_handler import find_canned_response, synthesize_speech
import os
from config import Config

def handle_incoming_call():
    """
    Generate TwiML to greet the caller and start recording their speech.
    """
    resp = VoiceResponse()
    # Greet or prompt the spam caller (could also play a tone or silence instead)
    resp.say("Hello, thanks for calling. Please hold while we connect you...", voice="alice", language="en")
    # Record the caller's voice. After recording, Twilio will hit the /voice/recording endpoint.
    resp.record(
        play_beep=True,
        max_length=30,  # record up to 30 seconds
        timeout=5,      # seconds of silence before stopping
        action="/voice/recording",  # where to send the recording (our Flask route)
        transcribe=False  # we'll use OpenAI for transcription instead of Twilio's service
    )
    # (Optionally, we could <Pause> or <Play> some hold music while recording.)
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
        log_conversation(caller_number, transcript_text=None, response_text="(no response, transcription failed)")
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
