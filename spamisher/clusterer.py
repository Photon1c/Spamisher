# clusterer.py
"""Cluster similar spam records."""

import hashlib
from typing import List, Optional
from spamisher.models import SpamRecord


def compute_cluster_hash(
    phone: str, domains: List[str], company: str, category: str
) -> str:
    """Create a simple hash for clustering."""
    parts = [
        phone or "",
        ",".join(sorted(domains)) if domains else "",
        company or "",
        category or "",
    ]
    hash_input = "|".join(parts)
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    return f"cluster_{hash_val}"


def assign_cluster(
    record: SpamRecord, existing_records: List[SpamRecord] = None
) -> Optional[str]:
    """Assign a cluster ID to a record based on similarity."""
    # Simple clustering: same phone, same URL, same company, or similar category
    if not existing_records:
        return record.cluster_id

    domains = [u.split("/")[2] for u in record.urls if u] if record.urls else []

    # Check for exact matches first
    for existing in existing_records:
        # Same phone number
        if existing.phone_number == record.phone_number:
            return existing.cluster_id

        # Same domain
        existing_domains = (
            [u.split("/")[2] for u in existing.urls if u] if existing.urls else []
        )
        if domains and existing_domains:
            if set(domains) & set(existing_domains):
                return existing.cluster_id

        # Same claimed company
        if existing.claimed_company and record.claimed_company:
            if existing.claimed_company.lower() == record.claimed_company.lower():
                return existing.cluster_id

    # Create new cluster
    return compute_cluster_hash(
        record.phone_number, domains, record.claimed_company, record.topic_category
    )


def get_cluster_summary(cluster_id: str, records: List[SpamRecord]) -> dict:
    """Get a summary of a cluster."""
    cluster_records = [r for r in records if r.cluster_id == cluster_id]

    if not cluster_records:
        return {}

    return {
        "cluster_id": cluster_id,
        "count": len(cluster_records),
        "phone_numbers": list(
            set(r.phone_number for r in cluster_records if r.phone_number)
        ),
        "categories": list(set(r.topic_category for r in cluster_records)),
        "risk_tags": list(set(tag for r in cluster_records for tag in r.risk_tags)),
        "avg_score": sum(r.confidence_score for r in cluster_records)
        / len(cluster_records),
    }
