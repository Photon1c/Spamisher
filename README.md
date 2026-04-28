# Spamisher

## AI Spam Call Handler

Spamisher is an AI-powered application that engages telemarketers in endless conversation loops, wasting their time and protecting you from unwanted calls.

![Logo](media/Spamisher.webp)

## Features

- AI-powered conversational agent that keeps telemarketers on the line
- Twilio voice integration for receiving and making calls
- Text-to-speech using either Twilio TTS or Neutts
- Speech-to-text via OpenAI Whisper
- LLM-powered response generation (OpenAI GPT models)
- Call logging and reporting capabilities

## Requirements

- Python 3.8+
- Twilio account (for voice calls)
- OpenAI API key (for LLM and speech-to-text)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/spamisher.git
cd spamisher
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and configure your variables:
```bash
cp .env.example .env
```

5. Edit `.env` with your API keys and phone numbers:
- `TWILIO_ACCOUNT_SID` - Your Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Your Twilio Auth Token
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number
- `MY_PHONE_NUMBER` - Your personal phone number to receive calls
- `OPENAI_API_KEY` - Your OpenAI API key

## Usage

Start the Flask application:
```bash
python src/app.py
```

The app will run on `http://localhost:5000` by default.

### Making a Call

1. Open the web interface at `http://localhost:5000`
2. Enter the spam caller's number
3. Click "Start Call" to begin engaging them

### Receiving Calls

Configure your Twilio webhook URL to point to your deployed endpoint `/voice` to receive incoming calls.

## Sample Procedure

**Spam Caller:** "Hi there, may I interest you in a warranty?"  
**Spamisher:** "Hii! That sounds super interesting. Tell me more"  

*Plenty of time has elapsed*  

**Spam caller:** "Sir, I am exhausted, I am going to have to hang up even though it is against company policy."  
**Spamisher:** "Noo :( plz stay, get your manager on the line if need be too."

*Logs number, runs Sherlock and OSINT on identifying caller data, emails user report, makes a report to the authorities*  

![art_2](media/spam_caller.webp)

## Project Structure

```
spamisher/
├── src/
│   ├── app.py           # Main Flask application
│   ├── routes.py        # Web routes
│   ├── config.py         # Configuration
│   ├── audio_handler.py # Audio processing
│   ├── twilio_handler.py# Twilio integration
│   └── openai_handler.py# OpenAI integration
├── spamisher/          # Core modules
│   ├── classifier.py
│   ├── clusterer.py
│   ├── normalizer.py
│   ├── scorer.py
│   └── models.py
├── media/               # Audio files
├── logs/                # Log files
└── tests/               # Test files
```

## Ethical Use

This technology is intended for defensive purposes—to protect individuals from harassing telemarketing calls. As always, ethical use of this code is expected. This technology is a pebble compared to the armament major conglomerates have at their disposal.

---

To run this project, entry point is `app.py`.
