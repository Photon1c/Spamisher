# classifier.py
"""Rule-based spam classifier."""

import re
from typing import List
from spamisher.models import CATEGORIES


# Category keywords mapping
CATEGORY_KEYWORDS = {
    "debt_collection": [
        "debt",
        "collection",
        "owed",
        "payment due",
        "overdue",
        "credit",
        " judgments",
    ],
    "warranty": [
        "warranty",
        "extended warranty",
        "car warranty",
        "vehicle",
        "coverage",
        "expired",
    ],
    "crypto": [
        "bitcoin",
        "crypto",
        "cryptocurrency",
        "blockchain",
        "btc",
        "ethereum",
        "token",
    ],
    "banking": [
        "bank",
        "account",
        "verify",
        "suspended",
        "unusual activity",
        "password",
        "login",
    ],
    "delivery": [
        "delivery",
        "package",
        "shipping",
        "fedex",
        "ups",
        "usps",
        "delivery failed",
    ],
    "tax": ["irs", "tax refund", "taxes", "internal revenue", "tax notice", "federal"],
    "healthcare": [
        "health",
        "medicare",
        "insurance",
        "medical",
        "prescription",
        "doctor",
    ],
    "political": ["poll", "vote", "election", "candidate", "campaign", "donation"],
    "phishing": [
        "verify your",
        "update your",
        "confirm your",
        "suspended",
        "click here",
    ],
}


def detect_category(message_text: str) -> str:
    """Detect spam category from message text."""
    if not message_text:
        return "unknown"

    text_lower = message_text.lower()
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return "unknown"

    return max(scores, key=scores.get)


def detect_risk_tags(message_text: str, urls: List[str] = None) -> List[str]:
    """Detect risk tags in the message."""
    if not message_text:
        return []

    text_lower = message_text.lower()
    tags = []

    # Contains URL
    if urls and len(urls) > 0:
        tags.append("contains_url")

    # Urgent language
    urgent_patterns = [
        "urgent",
        "immediately",
        "act now",
        "final notice",
        "expires today",
        "limited time",
        "24 hours",
    ]
    if any(p in text_lower for p in urgent_patterns):
        tags.append("urgent_language")

    # Payment request
    payment_patterns = [
        "pay",
        "payment",
        "credit card",
        "debit card",
        "fee",
        "cost",
        "charge",
    ]
    if any(p in text_lower for p in payment_patterns):
        tags.append("payment_request")

    # Crypto request
    crypto_patterns = ["bitcoin", "crypto", "send", "wallet", "transfer"]
    if any(p in text_lower for p in crypto_patterns):
        tags.append("crypto_request")

    # Gift card request
    gift_patterns = ["gift card", "itunes", "google play", "amazon gift"]
    if any(p in text_lower for p in gift_patterns):
        tags.append("gift_card_request")

    # Bank login request
    bank_patterns = [
        "verify your",
        "bank account",
        "login",
        "password",
        "ssn",
        "social security",
    ]
    if any(p in text_lower for p in bank_patterns):
        tags.append("bank_login_request")

    # Callback number
    phone_patterns = ["call back", "call us", "reach us at", "dial"]
    if any(p in text_lower for p in phone_patterns):
        tags.append("callback_number")

    return tags
