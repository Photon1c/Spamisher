# openai_handler.py
import openai, requests, os
from config import Config

# Set the OpenAI API key from config
openai.api_key = Config.OPENAI_API_KEY

def transcribe_audio(audio_url):
    """
    Download the audio from Twilio and use OpenAI's Whisper API to transcribe it.
    Returns the transcribed text, or None if transcription failed.
    """
    try:
        # Download the audio file from Twilio's URL
        resp = requests.get(audio_url + ".wav")  # Twilio gives recording URL without extension; append format
        audio_data = resp.content
        # Save to a temp file (OpenAI requires a file-like object)
        tmp_filename = "temp_recording.wav"
        with open(tmp_filename, "wb") as f:
            f.write(audio_data)
        # Use OpenAI's Whisper (speech-to-text)
        audio_file = open(tmp_filename, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        # Cleanup temp file
        os.remove(tmp_filename)
        # The OpenAI API returns an object with 'text'
        text = transcript.get("text") if isinstance(transcript, dict) else str(transcript)
        print(f"[Transcription] {text}")
        return text.strip()
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def generate_ai_reply(transcript_text):
    """
    Use OpenAI's language model to generate a response based on the caller's transcript.
    This could be a witty reply to a spam caller or any appropriate response.
    """
    try:
        prompt = (f"You are an automated call screener handling spam calls. "
                  f"The caller said: '{transcript_text}'. Respond with a brief, humorous reply.")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if available
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7
        )
        # Extract the assistant's reply
        reply_text = response['choices'][0]['message']['content'].strip()
        print(f"[AI Reply] {reply_text}")
        return reply_text
    except Exception as e:
        print(f"Error generating AI reply: {e}")
        return ""
