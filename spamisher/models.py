# models.py
"""Data models for spam records."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List


CATEGORIES = [
    "debt_collection",
    "warranty",
    "crypto",
    "banking",
    "delivery",
    "tax",
    "healthcare",
    "political",
    "phishing",
    "unknown",
]

RISK_TAGS = [
    "contains_url",
    "urgent_language",
    "payment_request",
    "crypto_request",
    "gift_card_request",
    "bank_login_request",
    "callback_number",
    "spoofed_caller_id",
    "voip_suspected",
    "repeat_phrase",
    "repeat_number",
    "repeat_domain",
]


@dataclass
class SpamRecord:
    id: str
    timestamp: str
    source_type: str  # call | sms | voicemail | manual
    phone_number: str
    raw_caller_id: Optional[str] = None
    cnam: Optional[str] = None
    message_text: str = ""
    voicemail_transcript: str = ""
    urls: List[str] = None
    claimed_company: Optional[str] = None
    topic_category: str = "unknown"
    risk_tags: List[str] = None
    confidence_score: float = 0.0
    cluster_id: Optional[str] = None
    user_action: str = "none"  # none | block | ignore | investigate | report
    notes: str = ""

    def __post_init__(self):
        if self.urls is None:
            self.urls = []
        if self.risk_tags is None:
            self.risk_tags = []

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


def new_record_id() -> str:
    """Generate a new record ID like spam_2026_04_27_001."""
    now = datetime.now()
    return f"spam_{now.strftime('%Y_%m_%d')}"


def get_risk_level(score: float) -> str:
    """Get risk level from score."""
    if score <= 25:
        return "low"
    elif score <= 50:
        return "medium"
    elif score <= 75:
        return "high"
    else:
        return "severe"
