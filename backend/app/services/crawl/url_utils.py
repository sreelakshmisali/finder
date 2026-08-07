"""
URL Utilities

Provides URL normalization (absolute resolution, tracking param stripping)
and in-session URL deduplication for the multi-stage crawl pipeline.
"""

import logging
from typing import Set, Optional
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse

logger = logging.getLogger(__name__)

# Tracking parameters to strip during normalization
_TRACKING_PARAMS: Set[str] = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid", "msclkid", "_ga", "trk", "source",
}

# URL schemes that are not navigable web pages
_SKIP_SCHEMES = {"mailto", "javascript", "tel", "ftp", "data"}


class URLNormalizer:
    """
    Normalizes raw URLs found in HTML pages into clean, canonical absolute URLs.
    """

    @staticmethod
    def normalize(raw_url: str, base_url: str = "") -> Optional[str]:
        """
        Resolves a raw URL (possibly relative) against a base URL,
        strips tracking params, and returns a canonical lowercase URL.

        Args:
            raw_url: The URL string as found in HTML (may be relative).
            base_url: The page URL to resolve relative hrefs against.

        Returns:
            Clean absolute URL string, or None if the URL is not navigable.
        """
        if not raw_url or not isinstance(raw_url, str):
            return None

        raw = raw_url.strip()

        # Skip non-navigable schemes
        for scheme in _SKIP_SCHEMES:
            if raw.lower().startswith(scheme + ":"):
                return None

        # Skip fragment-only links
        if raw.startswith("#"):
            return None

        # Resolve relative URLs against the base page URL
        if base_url and not raw.startswith(("http://", "https://", "//")):
            raw = urljoin(base_url, raw)
        elif raw.startswith("//"):
            raw = "https:" + raw

        try:
            parsed = urlparse(raw)
        except Exception:
            return None

        if not parsed.scheme or not parsed.netloc:
            return None

        if parsed.scheme not in ("http", "https"):
            return None

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default ports
        if scheme == "http" and netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif scheme == "https" and netloc.endswith(":443"):
            netloc = netloc[:-4]

        # Strip trailing slash from path (except root)
        path = parsed.path.rstrip("/") if parsed.path not in ("", "/") else "/"

        # Strip tracking query parameters and sort remaining
        query_dict = parse_qs(parsed.query, keep_blank_values=False)
        clean_query = {
            k: v for k, v in query_dict.items()
            if k.lower() not in _TRACKING_PARAMS
        }
        sorted_query = urlencode(
            sorted((k, v) for k, v_list in clean_query.items() for v in v_list)
        )

        # Reconstruct without fragment
        return urlunparse((scheme, netloc, path, parsed.params, sorted_query, ""))


class URLDeduplicator:
    """
    In-memory deduplicator for tracking seen URLs within a single crawl session.
    Prevents re-fetching or re-queuing the same URL multiple times.
    """

    def __init__(self):
        self._seen: Set[str] = set()

    def is_seen(self, url: str) -> bool:
        return url in self._seen

    def mark_seen(self, url: str) -> None:
        self._seen.add(url)

    def is_new(self, url: str) -> bool:
        """Returns True and marks seen if URL has not been seen before."""
        if url in self._seen:
            return False
        self._seen.add(url)
        return True

    def reset(self) -> None:
        self._seen.clear()

    @property
    def count(self) -> int:
        return len(self._seen)
