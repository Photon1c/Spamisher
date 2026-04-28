# Voice Capability Probe Tests

Tests that verify Twilio voice capabilities before building the full voice-agent system.

## Run Tests

```bash
pytest tests -q
```

## Tests

| Test | Description |
|------|-------------|
| `test_basic_voice_twiml_generation` | Verifies basic TwiML with `<Response>` and `<Say>` |
| `test_play_audio_twiml_generation` | Verifies `<Play>` TwiML (requires `SPAMISHER_TEST_AUDIO_URL`) |
| `test_gather_probe_twiml_generation` | Verifies `<Gather input="speech dtmf">` TwiML |
| `test_twilio_signature_validation_import` | Confirms Twilio SDK is importable |

## Environment Variables

- `SPAMISHER_TEST_AUDIO_URL` - Optional HTTPS URL for audio playback test