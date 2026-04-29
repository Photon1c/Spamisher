# openai_handler.py
"""Handler for transcription and AI replies using configurable providers."""

import openai, requests, os
from src.config import Config
from src.model_config import ModelConfig, ProviderBase


def capture_output(output_type: str, content: str, metadata: dict = None):
    """Save output to disk if CAPTURE_OUTPUTS is enabled."""
    if not ModelConfig.CAPTURE_OUTPUTS:
        return

    os.makedirs(ModelConfig.OUTPUT_DIR, exist_ok=True)
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_type}_{timestamp}.json"
    filepath = os.path.join(ModelConfig.OUTPUT_DIR, filename)

    # Sanitize sensitive values
    safe_metadata = {}
    if metadata:
        for k, v in metadata.items():
            if (
                "token" not in k.lower()
                and "key" not in k.lower()
                and "phone" not in k.lower()
            ):
                safe_metadata[k] = v

    data = {
        "type": output_type,
        "content": content,
        "metadata": safe_metadata,
        "timestamp": timestamp,
    }

    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save output: {e}")


def transcribe_audio(audio_url):
    """
    Download the audio from Twilio and use OpenAI's Whisper API to transcribe it.
    Returns the transcribed text, or None if transcription failed.
    """
    try:
        from openai import OpenAI
        from config import Config

        resp = requests.get(audio_url + ".wav")
        audio_data = resp.content
        tmp_filename = "temp_recording.wav"
        with open(tmp_filename, "wb") as f:
            f.write(audio_data)

        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        with open(tmp_filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file
            )
        os.remove(tmp_filename)
        text = transcript.text
        result = text.strip()
        print(f"[Transcription] {result}")
        capture_output("transcription", result, {"audio_url": audio_url})
        return result
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None


def generate_ai_reply(transcript_text):
    """
    Use configurable LLM provider to generate a response.
    Uses ModelConfig to pick provider.
    """
    try:
        system_prompt = "You are an automated call screener handling spam calls. Respond with a brief, humorous reply."
        prompt = f"The caller said: '{transcript_text}'. Respond with a brief, humorous reply."

        provider = ModelConfig.get_llm_provider()
        reply_text = provider.generate(prompt, system_prompt)

        print(f"[AI Reply] {reply_text}")
        capture_output("ai_reply", reply_text, {"transcript": transcript_text})
        return reply_text
    except Exception as e:
        print(f"Error generating AI reply: {e}")
        return ""
