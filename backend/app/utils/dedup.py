"""
Duplicate Detection Utility

Provides content hashing to identify duplicate job postings originating from
different job boards or providers.
"""

import hashlib
import re


function_description = """
Generates a deterministic SHA-256 hash string from a job's company, title, and location.

Why content hashing?
- The same job (e.g. "Senior Backend Engineer" at "Stripe") might be listed on multiple boards.
- Comparing raw strings can fail due to whitespace or case differences.
- Normalizing company, title, and location into a standard lowercase representation
  before hashing yields an identical fingerprint for duplicate postings.

Args:
    company: Company name (e.g., "Stripe, Inc.")
    title: Job title (e.g., "Senior Backend Engineer (Remote)")
    location: Job location (e.g., "San Francisco, CA")

Returns:
    64-character SHA-256 hex string uniquely identifying this job concept.
"""


def generate_content_hash(company: str, title: str, location: str) -> str:
    """
    Generate SHA-256 fingerprint from job core metadata.
    """
    # Clean and normalize strings (lowercase, remove extra punctuation and spaces)
    norm_company = re.sub(r"[^\w\s]", "", company.strip().lower())
    norm_title = re.sub(r"[^\w\s]", "", title.strip().lower())
    norm_location = re.sub(r"[^\w\s]", "", location.strip().lower())

    raw_fingerprint = f"{norm_company}|{norm_title}|{norm_location}"
    return hashlib.sha256(raw_fingerprint.encode("utf-8")).hexdigest()
