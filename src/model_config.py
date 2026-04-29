# model_config.py
"""
Unified configuration for LLM and TTS providers.
Supports switching between providers without code changes.
"""

import os
import subprocess
import uuid
from typing import List, Optional
from twilio.twiml.voice_response import VoiceResponse


class ModelConfig:
    # LLM Provider selection
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "60"))
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    LOCAL_MODEL_URL = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434")
    LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "llama2")

    # TTS Provider selection
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "twilio")
    NEUTTS_API_KEY = os.getenv("NEUTTS_API_KEY", "")
    NEUTTS_VOICE = os.getenv("NEUTTS_VOICE", "amy")

    # Output capture settings
    CAPTURE_OUTPUTS = os.getenv("CAPTURE_OUTPUTS", "false").lower() == "true"
    OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")

    @classmethod
    def get_llm_provider(cls):
        if cls.LLM_PROVIDER == "openai":
            return OpenAIProvider()
        elif cls.LLM_PROVIDER == "local":
            return LocalProvider()
        elif cls.LLM_PROVIDER == "mock":
            return MockProvider()
        else:
            return OpenAIProvider()

    @classmethod
    def get_tts_provider(cls):
        if cls.TTS_PROVIDER == "twilio":
            return TwilioTTSProvider()
        elif cls.TTS_PROVIDER == "neutts":
            return NeuttsProvider()
        else:
            return TwilioTTSProvider()


class ProviderBase:
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        raise NotImplementedError


class OpenAIProvider(ProviderBase):
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        from config import Config
        from openai import OpenAI

        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=ModelConfig.OPENAI_MODEL,
            messages=messages,
            max_tokens=ModelConfig.OPENAI_MAX_TOKENS,
            temperature=ModelConfig.OPENAI_TEMPERATURE,
        )
        return response.choices[0].message.content.strip()


class LocalProvider(ProviderBase):
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        import requests

        url = f"{ModelConfig.LOCAL_MODEL_URL}/api/generate"
        payload = {
            "model": ModelConfig.LOCAL_MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        }
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json().get("response", "")


class MockProvider(ProviderBase):
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        return f"Mock response to: {prompt[:50]}..."


class TTSProviderBase:
    def synthesize(self, text: str, voice: str = "alice") -> str:
        raise NotImplementedError


class TwilioTTSProvider(TTSProviderBase):
    def synthesize(self, text: str, voice: str = "alice") -> str:
        resp = VoiceResponse()
        resp.say(text, voice=voice)
        return str(resp)


class NeuttsProvider(TTSProviderBase):
    """Neutts voice cloning TTS provider."""

    def _trim_silence(self, path):
        """Simple threshold-based trimming for Neutts output."""
        import wave
        import struct

        try:
            with wave.open(path, "rb") as wav:
                params = wav.getparams()
                frames = wav.readframes(params.nframes)

            # Neutts usually outputs 16-bit PCM
            samples = struct.unpack(f"<{len(frames) // 2}h", frames)

            # DYNAMIC THRESHOLD: Use 10% of max amplitude instead of hardcoded 500
            max_amp = max(abs(s) for s in samples) if samples else 0
            threshold = max(200, int(max_amp * 0.1))

            print(
                f"[DEBUG] Trimming audio (Max Amp: {max_amp}, Threshold: {threshold})"
            )

            start_idx = 0
            for i, s in enumerate(samples):
                if abs(s) > threshold:
                    start_idx = i
                    break

            end_idx = len(samples)
            for i, s in enumerate(reversed(samples)):
                if abs(s) > threshold:
                    end_idx = len(samples) - i
                    break

            # Add 0.2s padding (increased from 0.1s for smoother start/end)
            padding = int(params.framerate * 0.2)
            start_idx = max(0, start_idx - padding)
            end_idx = min(len(samples), end_idx + padding)

            trimmed_samples = samples[start_idx:end_idx]

            # SAFETY CHECK: If we trimmed away too much, revert to original
            if (
                len(trimmed_samples) < params.framerate * 0.5
            ):  # Less than 0.5s remaining
                print("[DEBUG] Trimming too aggressive, keeping original file.")
                return

            trimmed_frames = struct.pack(f"<{len(trimmed_samples)}h", *trimmed_samples)

            with wave.open(path, "wb") as wav:
                wav.setparams(params)
                wav.writeframes(trimmed_frames)
            print(
                f"[DEBUG] Audio trimmed: {len(samples)} -> {len(trimmed_samples)} samples"
            )
        except Exception as e:
            print(f"[DEBUG] Trimming failed: {e}")

    def synthesize(self, text: str, voice: str = None) -> str:
        """Generate audio using Neutts voice cloning."""
        from config import Config

        voice = voice or Config.NEUTTS_VOICE
        neutts_path = os.path.expanduser(Config.NEUTTS_PATH)
        samples_dir = os.path.join(neutts_path, "samples")

        ref_audio = os.path.join(samples_dir, f"{voice}.wav")
        ref_text_path = os.path.join(samples_dir, f"{voice}.txt")

        if not os.path.exists(ref_audio):
            resp = VoiceResponse()
            resp.say(text, voice="alice")
            return str(resp)

        # Read reference text if it exists to pass as a string (more reliable than path)
        ref_text_val = ""
        if os.path.exists(ref_text_path):
            try:
                with open(ref_text_path, "r") as f:
                    ref_text_val = f.read().strip()
            except:
                pass

        if not ref_text_val:
            # Fallback for known voices
            ref_defaults = {"jo": "Hello, my name is Jo.", "amy": "Hello, I am Amy."}
            ref_text_val = ref_defaults.get(voice, "Hello there.")

        # Generate audio
        output_dir = Config.NEUTTS_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)

        output_filename = f"neutts_{voice}_{uuid.uuid4().hex[:8]}.wav"
        output_path = os.path.join(output_dir, output_filename)

        # Use neuttsenv python with absolute paths
        neutts_python = os.path.expanduser("~/envs/neuttsenv/bin/python")
        neutts_example = os.path.join(neutts_path, "examples", "basic_example.py")

        # Ensure absolute paths
        ref_audio_abs = os.path.abspath(ref_audio)
        output_path_abs = os.path.abspath(output_path)

        try:
            print(f"[DEBUG] Executing Neutts synthesis for voice: {voice}")
            print(f"[DEBUG] Input Text: {text}")
            result = subprocess.run(
                [
                    neutts_python,
                    neutts_example,
                    "--input_text",
                    text,
                    "--ref_audio",
                    ref_audio_abs,
                    "--ref_text",
                    ref_text_val,
                    "--output_path",
                    output_path_abs,
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0 and os.path.exists(output_path):
                # Trim silence from the generated audio
                self._trim_silence(output_path)

                # HIGH FIDELITY MP3 FOR TUNNEL STABILITY
                # Using 44.1kHz to match standard browser/telephony expectations for MP3
                # but mono to keep it light.
                telephony_path = output_path.replace(".wav", ".mp3")
                telephony_filename = output_filename.replace(".wav", ".mp3")
                try:
                    # ffmpeg conversion with high quality libmp3lame
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            output_path,
                            "-codec:a",
                            "libmp3lame",
                            "-ar",
                            "44100",
                            "-ac",
                            "1",
                            "-b:a",
                            "128k",
                            telephony_path,
                        ],
                        capture_output=True,
                        check=True,
                    )
                    final_path = telephony_path
                    final_filename = telephony_filename
                    print(f"[DEBUG] Converted to High-Fidelity MP3 (44.1k/128k).")
                except Exception as e:
                    print(f"[DEBUG] MP3 Conversion failed: {e}. Using original.")
                    final_path = output_path
                    final_filename = output_filename

                resp = VoiceResponse()
                try:
                    from src.config import Config
                    from flask import request as flask_request

                    # Priority: 1. EXTERNAL_URL from config, 2. Host header, 3. Relative
                    base_url = Config.EXTERNAL_URL
                    if (
                        not base_url
                        and flask_request
                        and hasattr(flask_request, "host_url")
                    ):
                        base_url = flask_request.host_url.rstrip("/")

                    if base_url:
                        audio_url = f"{base_url.rstrip('/')}/media/{final_filename}"
                    else:
                        audio_url = f"/media/{final_filename}"
                except Exception as e:
                    print(f"[DEBUG] URL construction failed: {e}")
                    audio_url = f"/media/{final_filename}"

                print(f"[DEBUG] Neutts success. Playing: {audio_url}")
                # Use a very short pause just to let the socket open
                resp.pause(length=1)
                resp.play(audio_url)
                return str(resp)
            else:
                print(
                    f"Neutts error (returncode {result.returncode}): {result.stderr[:500]}"
                )
        except subprocess.TimeoutExpired:
            print(f"Neutts error: Synthesis timed out after 300 seconds.")
        except Exception as e:
            print(f"Neutts error: {e}")

        # Fallback to Twilio
        resp = VoiceResponse()
        resp.say(text, voice="alice")
        return str(resp)
