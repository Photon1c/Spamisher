# audio_handler.py
import os

# Assume we have a folder 'static/audio' with some canned response files.
CANNED_RESPONSES = {
    # keyword or phrase : filename of canned response audio
    "warranty": "static/audio/car_warranty_response.mp3",
    "IRS": "static/audio/fake_irs_response.mp3",
    # ... add more as needed
}

def find_canned_response(transcript_text):
    """
    Check transcript for known spam keywords to select a canned response.
    Returns the file path of a canned audio response if found, otherwise None.
    """
    if not transcript_text:
        return None
    text_lower = transcript_text.lower()
    for keyword, audio_path in CANNED_RESPONSES.items():
        if keyword.lower() in text_lower:
            # We found a keyword triggering a canned response
            if os.path.exists(audio_path):
                return audio_path
    return None

def synthesize_speech(text):
    """
    (Optional) Synthesize speech from text if we want custom TTS.
    For now, we rely on Twilio <Say>, so this can be a placeholder.
    """
    # In future, integrate AWS Polly or Google TTS to get an MP3 file for the text.
    # For now, just return None to indicate we should use Twilio's <Say>.
    return None
