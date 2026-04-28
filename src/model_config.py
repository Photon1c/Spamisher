# model_config.py
"""
Unified configuration for LLM and TTS providers.
Supports switching between providers without code changes.
"""

import os


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
        from twilio.twiml.voice_response import VoiceResponse

        resp = VoiceResponse()
        resp.say(text, voice=voice)
        return str(resp)


class NeuttsProvider(TTSProviderBase):
    """Neutts voice cloning TTS provider."""

    def synthesize(self, text: str, voice: str = None) -> str:
        """Generate audio using Neutts voice cloning."""
        import uuid
        import subprocess

        from config import Config
        from twilio.twiml.voice_response import VoiceResponse

        voice = voice or Config.NEUTTS_VOICE
        neutts_path = os.path.expanduser(Config.NEUTTS_PATH)
        samples_dir = os.path.join(neutts_path, "samples")

        ref_audio = os.path.join(samples_dir, f"{voice}.wav")
        ref_text_path = os.path.join(samples_dir, f"{voice}.txt")

        if not os.path.exists(ref_audio):
            resp = VoiceResponse()
            resp.say(text, voice="alice")
            return str(resp)

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
        ref_text_abs = os.path.abspath(ref_text_path)
        output_path_abs = os.path.abspath(output_path)

        try:
            result = subprocess.run(
                [
                    neutts_python,
                    neutts_example,
                    "--input_text",
                    text,
                    "--ref_audio",
                    ref_audio_abs,
                    "--ref_text",
                    ref_text_abs,
                    "--output_path",
                    output_path_abs,
                ],
                capture_output=True,
                timeout=120,
            )

            if result.returncode == 0 and os.path.exists(output_path):
                resp = VoiceResponse()
                resp.play(f"/media/{output_filename}")
                return str(resp)
            else:
                print(f"Neutts error: {result.stderr.decode()[:200]}")
        except Exception as e:
            print(f"Neutts error: {e}")

        # Fallback to Twilio
        resp = VoiceResponse()
        resp.say(text, voice="alice")
        return str(resp)
