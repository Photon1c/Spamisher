"""Expanded test suite for Spamisher routes and model config."""

import pytest
import os


class TestBasicVoiceTwiML:
    def test_basic_voice_twiml_generation(self):
        """Test basic TwiML response contains required elements."""
        from src.twilio_handler import handle_incoming_call

        twiml = handle_incoming_call()
        xml_str = str(twiml)

        assert "<Response>" in xml_str
        assert "<Say" in xml_str
        assert "Hello" in xml_str


class TestPlayAudioTwiML:
    def test_play_audio_twiml_generation(self):
        """Test TwiML with <Play> element for audio playback."""
        from twilio.twiml.voice_response import VoiceResponse

        audio_url = os.environ.get("SPAMISHER_TEST_AUDIO_URL")
        if not audio_url:
            pytest.skip("SPAMISHER_TEST_AUDIO_URL not set")

        resp = VoiceResponse()
        resp.play(audio_url)
        xml_str = str(resp)

        assert "<Play>" in xml_str
        assert audio_url in xml_str


class TestGatherTwiML:
    def test_gather_probe_twiml_generation(self):
        """Test TwiML with <Gather> for speech/dtmf input collection."""
        from twilio.twiml.voice_response import VoiceResponse

        resp = VoiceResponse()
        with resp.gather(input="speech dtmf", timeout=10) as gather:
            gather.say("Please speak or press digits.")
        resp.say("No input received.")

        xml_str = str(resp)
        assert "<Gather" in xml_str
        assert "speech" in xml_str
        assert "dtmf" in xml_str


class TestTwilioSignatureValidation:
    def test_twilio_signature_validation_import(self):
        """Verify Twilio request validator can be imported."""
        try:
            from twilio.request_validator import RequestValidator
        except ImportError:
            pytest.skip("twilio package not installed")


class TestModelConfig:
    def test_model_config_import(self):
        """Verify model_config loads."""
        from src.model_config import ModelConfig

        assert ModelConfig.LLM_PROVIDER in ["openai", "local", "mock"]
        assert ModelConfig.TTS_PROVIDER in ["twilio", "neutts", "mock"]

    def test_mock_provider(self):
        """Test mock provider returns text."""
        from src.model_config import MockProvider

        provider = MockProvider()
        result = provider.generate("test prompt")
        assert "test prompt" in result
        assert len(result) > 0

    def test_twilio_tts_provider(self):
        """Test Twilio TTS provider returns TwiML."""
        from src.model_config import TwilioTTSProvider

        provider = TwilioTTSProvider()
        result = provider.synthesize("Hello world", "alice")
        assert "<Say" in result
        assert "Hello world" in result


class TestRoutes:
    def test_voice_probe_route(self):
        """Test /voice/probe returns TwiML."""
        from src.app import app

        with app.test_client() as client:
            res = client.post("/voice/probe")
            assert res.status_code == 200
            assert b"<Response>" in res.data

    def test_voice_tts_route(self):
        """Test /voice/tts returns TwiML."""
        from src.app import app

        with app.test_client() as client:
            res = client.post("/voice/tts", data={"text": "Test message"})
            assert res.status_code == 200
            assert b"<Say" in res.data

    def test_voice_status_route(self):
        """Test /voice/status returns JSON."""
        from src.app import app

        with app.test_client() as client:
            res = client.get("/voice/status")
            assert res.status_code == 200
            import json

            data = json.loads(res.data)
            assert "twilio" in data
            assert "openai" in data

    def test_index_route(self):
        """Test / returns HTML."""
        from src.app import app

        with app.test_client() as client:
            res = client.get("/")
            assert res.status_code == 200
            assert b"<!DOCTYPE html>" in res.data or b"<html" in res.data


class TestOpenAIHandler:
    def test_mock_provider_direct(self):
        """Test mock provider directly (not via model_config to avoid import caching)."""
        from src.model_config import MockProvider

        provider = MockProvider()
        result = provider.generate("test prompt")
        assert "test prompt" in result
