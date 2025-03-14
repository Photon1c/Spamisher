# app.py
from flask import Flask
from config import Config

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)  # load configuration from Config class

# Import and register routes (to avoid circular imports)
from routes import voice_bp
app.register_blueprint(voice_bp)  # register blueprint for Twilio voice routes

# (Optional) Additional blueprints for future features can be registered similarly.

if __name__ == "__main__":
    # Run the app in debug mode for local testing
    app.run(host="0.0.0.0", port=5000, debug=app.config['DEBUG'])
