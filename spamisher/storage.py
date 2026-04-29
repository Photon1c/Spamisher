# storage.py
"""Storage for spam records in JSONL format."""

import json
import os
from typing import List, Optional
from pathlib import Path
from spamisher.models import SpamRecord


DATA_DIR = Path(__file__).parent.parent / "data"
RECORDS_FILE = DATA_DIR / "spam_records.jsonl"
CLUSTERS_FILE = DATA_DIR / "spam_clusters.json"
CALLS_FILE = DATA_DIR / "call_logs.jsonl"


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)


def save_call_log(log: SpamRecord) -> str:
    """Save a call log to JSONL file."""
    ensure_data_dir()

    with open(CALLS_FILE, "a") as f:
        f.write(json.dumps(log.to_dict()) + "\n")

    return log.sid


def load_call_logs() -> List[dict]:
    """Load all call logs from JSONL file."""
    logs = []

    if not CALLS_FILE.exists():
        return logs

    with open(CALLS_FILE, "r") as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(json.loads(line.strip()))
                except Exception:
                    pass

    return logs


def save_record(record: SpamRecord) -> str:
    """Save a spam record to JSONL file."""
    ensure_data_dir()

    with open(RECORDS_FILE, "a") as f:
        f.write(json.dumps(record.to_dict()) + "\n")

    return record.id


def load_records() -> List[SpamRecord]:
    """Load all spam records from JSONL file."""
    records = []

    if not RECORDS_FILE.exists():
        return records

    with open(RECORDS_FILE, "r") as f:
        for line in f:
            if line.strip():
                try:
                    d = json.loads(line.strip())
                    records.append(SpamRecord.from_dict(d))
                except Exception:
                    pass

    return records


def get_record(record_id: str) -> Optional[SpamRecord]:
    """Get a specific record by ID."""
    records = load_records()
    for record in records:
        if record.id == record_id:
            return record
    return None


def save_clusters(clusters: dict) -> None:
    """Save cluster summaries to JSON file."""
    ensure_data_dir()

    with open(CLUSTERS_FILE, "w") as f:
        json.dump(clusters, f, indent=2)


def load_clusters() -> dict:
    """Load cluster summaries from JSON file."""
    if not CLUSTERS_FILE.exists():
        return {}

    with open(CLUSTERS_FILE, "r") as f:
        return json.load(f)


def add_record(record: SpamRecord) -> SpamRecord:
    """Add a complete record: normalize, classify, score, cluster, save."""
    from spamisher.classifier import detect_category, detect_risk_tags
    from spamisher.scorer import calculate_score
    from spamisher.clusterer import assign_cluster

    # Classify
    full_text = record.message_text + " " + record.voicemail_transcript
    record.topic_category = detect_category(full_text)
    record.risk_tags = detect_risk_tags(full_text, record.urls)

    # Score
    record.confidence_score = calculate_score(record)

    # Load existing and assign cluster
    existing = load_records()
    record.cluster_id = assign_cluster(record, existing)

    # Save
    save_record(record)

    return record
