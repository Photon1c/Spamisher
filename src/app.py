# app.py
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file FIRST, before importing config
load_dotenv("/home/sherlockhums/apps/spamisher/.env")

from flask import Flask, send_from_directory, make_response
from src.config import Config

# Initialize Flask application
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.from_object(Config)
app.config["FLASK_RUN_PORT"] = 6005


@app.route("/favicon.ico")
def favicon():
    """Serve the site favicon."""
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# Create media directory if it doesn't exist
media_dir = os.path.expanduser("~/apps/spamisher/media")
os.makedirs(media_dir, exist_ok=True)


@app.route("/media/<path:filename>")
def serve_media(filename):
    response = make_response(send_from_directory(media_dir, filename))
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    if filename.endswith(".mp3"):
        response.headers["Content-Type"] = "audio/mpeg"
    else:
        response.headers["Content-Type"] = "audio/wav"

    response.headers["Content-Disposition"] = "inline"
    response.headers["Accept-Ranges"] = "bytes"  # Crucial for Twilio streaming

    return response


# Import and register routes
from src.routes import voice_bp

app.register_blueprint(voice_bp)


# CLI commands for spam management
def cli_main():
    if len(sys.argv) < 2:
        print("Usage: python app.py <command> [args]")
        print("Commands: add, list, clusters, show")
        return

    cmd = sys.argv[1]

    if cmd == "add":
        _cli_add()
    elif cmd == "list":
        _cli_list()
    elif cmd == "clusters":
        _cli_clusters()
    elif cmd == "show":
        _cli_show()
    else:
        print(f"Unknown command: {cmd}")


def _cli_add():
    import argparse
    from spamisher.normalizer import normalize_record
    from spamisher.storage import add_record
    from spamisher.models import get_risk_level

    parser = argparse.ArgumentParser(description="Add a spam record")
    parser.add_argument(
        "--source", default="manual", help="Source type (call/sms/voicemail/manual)"
    )
    parser.add_argument("--phone", required=True, help="Phone number")
    parser.add_argument("--text", default="", help="Message text")
    parser.add_argument("--transcript", default="", help="Voicemail transcript")
    args = parser.parse_args(sys.argv[2:])

    record = normalize_record(
        source_type=args.source,
        phone_number=args.phone,
        message_text=args.text,
        voicemail_transcript=args.transcript,
    )

    record = add_record(record)

    print(f"Saved spam record: {record.id}")
    print(f"Category: {record.topic_category}")
    print(f"Risk level: {get_risk_level(record.confidence_score)}")
    print(f"Score: {record.confidence_score}")
    print(f"Cluster: {record.cluster_id}")


def _cli_list():
    from spamisher.storage import load_records

    records = load_records()
    if not records:
        print("No records found.")
        return

    print(f"Total records: {len(records)}\n")
    for r in records[-10:]:
        print(
            f"{r.id} | {r.source_type} | {r.phone_number} | {r.topic_category} | score:{r.confidence_score} | {r.cluster_id}"
        )


def _cli_clusters():
    from spamisher.storage import load_records, load_clusters
    from spamisher.models import SpamRecord

    records = load_records()
    if not records:
        print("No clusters found.")
        return

    clusters = {}
    for r in records:
        if r.cluster_id:
            if r.cluster_id not in clusters:
                clusters[r.cluster_id] = []
            clusters[r.cluster_id].append(r)

    print(f"Total clusters: {len(clusters)}\n")
    for cid, recs in clusters.items():
        avg_score = sum(r.confidence_score for r in recs) / len(recs)
        print(f"{cid} | {len(recs)} records | avg score: {avg_score:.1f}")


def _cli_show():
    import argparse
    from spamisher.storage import get_record

    parser = argparse.ArgumentParser(description="Show a spam record")
    parser.add_argument("id", help="Record ID")
    args = parser.parse_args(sys.argv[2:])

    record = get_record(args.id)
    if not record:
        print(f"Record not found: {args.id}")
        return

    print(f"ID: {record.id}")
    print(f"Timestamp: {record.timestamp}")
    print(f"Source: {record.source_type}")
    print(f"Phone: {record.phone_number}")
    print(f"Category: {record.topic_category}")
    print(f"Score: {record.confidence_score}")
    print(f"Cluster: {record.cluster_id}")
    print(f"Risk tags: {', '.join(record.risk_tags)}")
    print(f"Message: {record.message_text[:100]}...")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in ["run", "serve"]:
        cli_main()
    else:
        app.run(host="0.0.0.0", port=6005, debug=app.config["DEBUG"])
