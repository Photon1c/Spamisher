# scorer.py
"""Confidence scoring for spam records."""

from typing import List
from spamisher.models import SpamRecord, get_risk_level


# Scoring weights for each tag
TAG_SCORES = {
    "contains_url": 20,
    "urgent_language": 15,
    "payment_request": 20,
    "crypto_request": 25,
    "gift_card_request": 20,
    "bank_login_request": 25,
    "callback_number": 10,
    "spoofed_caller_id": 20,
    "voip_suspected": 10,
    "repeat_phrase": 15,
    "repeat_number": 15,
    "repeat_domain": 20,
}


def calculate_score(record: SpamRecord) -> float:
    """Calculate confidence score for a spam record."""
    score = 0

    # Add scores from risk tags
    for tag in record.risk_tags:
        score += TAG_SCORES.get(tag, 0)

    # Bonus for unverified company claiming
    if record.claimed_company and not record.phone_number:
        score += 10

    # Cap at 100
    return min(score, 100.0)


def classify_record(record: SpamRecord) -> SpamRecord:
    """Add classification results to a record."""
    from .classifier import detect_category, detect_risk_tags

    # Detect category
    full_text = record.message_text + " " + record.voicemail_transcript
    record.topic_category = detect_category(full_text)

    # Detect risk tags
    record.risk_tags = detect_risk_tags(full_text, record.urls)

    # Calculate score
    record.confidence_score = calculate_score(record)

    return record
