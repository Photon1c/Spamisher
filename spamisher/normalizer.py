# normalizer.py
"""Normalize spam inputs into structured records."""

import re
from urllib.parse import urlparse
from typing import List, Optional
from spamisher.models import SpamRecord, new_record_id
from datetime import datetime


def normalize_phone(number: str) -> Optional[str]:
    """Normalize phone number to E.164 format."""
    if not number:
        return None
    digits = re.sub(r"\D", "", number)
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"+{digits}"
    elif len(digits) >= 10:
        return f"+{digits}"
    return None


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    if not text:
        return []
    url_pattern = re.compile(r"https?://[^\s]+")
    return url_pattern.findall(text)


def extract_domains(urls: List[str]) -> List[str]:
    """Extract domains from URLs."""
    domains = []
    for url in urls:
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                domains.append(parsed.netloc)
        except Exception:
            pass
    return domains


def extract_phone_numbers(text: str) -> List[str]:
    """Extract all phone numbers from text."""
    if not text:
        return []
    phone_pattern = re.compile(r"\+?1?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}")
    numbers = phone_pattern.findall(text)
    return [normalize_phone(n) for n in numbers if normalize_phone(n)]


def extract_company(text: str) -> Optional[str]:
    """Try to extract claimed company name."""
    if not text:
        return None
    # Common patterns like "This is X from company" or "company Inc"
    patterns = [
        r"(?:from|at|with|representing)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
        r"([A-Z][a-zA-Z]+)\s+(?:Inc|corp|company|llc)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def normalize_record(
    source_type: str,
    phone_number: str,
    message_text: str = "",
    voicemail_transcript: str = "",
    raw_caller_id: str = None,
) -> SpamRecord:
    """Create a normalized spam record from raw inputs."""
    record_id = new_record_id()
    timestamp = datetime.now().isoformat()

    normalized_phone = normalize_phone(phone_number)
    urls = extract_urls(message_text or voicemail_transcript)
    domains = extract_domains(urls)
    claimed_company = extract_company(message_text or voicemail_transcript)

    return SpamRecord(
        id=record_id,
        timestamp=timestamp,
        source_type=source_type,
        phone_number=normalized_phone or phone_number,
        raw_caller_id=raw_caller_id,
        message_text=message_text,
        voicemail_transcript=voicemail_transcript,
        urls=urls,
        claimed_company=claimed_company,
    )
