"""Tests for spamisher package."""

import pytest
import sys
import os

# Add the spamisher package to path
spamisher_path = os.path.join(os.path.dirname(__file__), "..", "spamisher")
sys.path.insert(0, spamisher_path)


class TestNormalizer:
    def test_normalize_phone_10digit(self):
        from normalizer import normalize_phone

        result = normalize_phone("2065550123")
        assert result == "+12065550123"

    def test_normalize_phone_with_plus(self):
        from normalizer import normalize_phone

        result = normalize_phone("+1 206-555-0123")
        assert result == "+12065550123"

    def test_extract_urls(self):
        from normalizer import extract_urls

        text = "Visit https://example.com now"
        urls = extract_urls(text)
        assert "https://example.com" in urls

    def test_extract_domains(self):
        from normalizer import extract_domains

        urls = ["https://example.com/path", "https://test.org/page"]
        domains = extract_domains(urls)
        assert "example.com" in domains
        assert "test.org" in domains


class TestClassifier:
    def test_detect_category_warranty(self):
        from classifier import detect_category

        text = "Your car warranty is about to expire"
        cat = detect_category(text)
        assert cat == "warranty"

    def test_detect_category_crypto(self):
        from classifier import detect_category

        text = "Send bitcoin to wallet address"
        cat = detect_category(text)
        assert cat == "crypto"

    def test_detect_risk_tags_url(self):
        from classifier import detect_risk_tags
        from normalizer import extract_urls

        text = "Visit https://example.com now"
        urls = extract_urls(text)
        tags = detect_risk_tags(text, urls)
        assert "contains_url" in tags

    def test_detect_risk_tags_urgent(self):
        from classifier import detect_risk_tags

        text = "Act immediately or lose it"
        tags = detect_risk_tags(text)
        assert "urgent_language" in tags


class TestScorer:
    def test_calculate_score(self):
        from scorer import calculate_score
        from models import SpamRecord

        record = SpamRecord(
            id="test_001",
            timestamp="2026-04-27T12:00:00",
            source_type="sms",
            phone_number="+12065550123",
            risk_tags=["contains_url", "urgent_language"],
        )
        score = calculate_score(record)
        assert score == 35  # 20 + 15


class TestModels:
    def test_get_risk_level(self):
        from models import get_risk_level

        assert get_risk_level(20) == "low"
        assert get_risk_level(30) == "medium"
        assert get_risk_level(60) == "high"
        assert get_risk_level(90) == "severe"

    def test_record_to_dict(self):
        from models import SpamRecord

        record = SpamRecord(
            id="test_001",
            timestamp="2026-04-27T12:00:00",
            source_type="sms",
            phone_number="+12065550123",
        )
        d = record.to_dict()
        assert d["id"] == "test_001"
        assert d["phone_number"] == "+12065550123"
