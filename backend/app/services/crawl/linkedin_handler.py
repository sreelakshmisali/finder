"""
LinkedIn HTML Parser

Robust pure HTML parser for LinkedIn job postings.
Performs ZERO HTTP requests. Consumes raw HTML strings directly.
"""

import re
import json
import urllib.parse
from typing import Optional, Tuple
from bs4 import BeautifulSoup


class LinkedInHandler:
    """
    Robust pure HTML parser for LinkedIn job postings.
    Performs ZERO HTTP requests.
    Consumes raw_html string directly.
    """

    @classmethod
    def parse_linkedin_html(cls, raw_html: str, page_url: str) -> Tuple[Optional[str], bool]:
        """
        Parses raw_html of a LinkedIn page to detect external apply URLs or Easy Apply.
        Executed inside JobExtractor.extract_from_url() BEFORE HTML cleaning/extraction.

        Returns:
            (external_apply_url: Optional[str], is_easy_apply: bool)
        """
        if not raw_html:
            return None, False

        soup = BeautifulSoup(raw_html, "html.parser")

        # Strategy 1: JSON-LD Structured Data (@type=JobPosting -> applyAction)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    if data.get("@type") == "JobPosting":
                        apply_action = data.get("applyAction", {})
                        if isinstance(apply_action, dict) and apply_action.get("target"):
                            target = apply_action["target"]
                            if "linkedin.com" not in target:
                                return target.strip(), False
            except Exception:
                continue

        # Strategy 2: Offsite tracking attributes
        offsite_btn = soup.find("a", {"data-tracking-control-name": re.compile(r"offsite|apply", re.I)})
        if offsite_btn and offsite_btn.get("href"):
            href = offsite_btn["href"].strip()
            if "linkedin.com" not in href:
                return href, False

        # Strategy 3: Redirect query parameters
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "linkedin.com/redir/" in href or "url=" in href:
                match = re.search(r"[?&]url=([^&]+)", href)
                if match:
                    unquoted = urllib.parse.unquote(match.group(1))
                    if "linkedin.com" not in unquoted:
                        return unquoted.strip(), False

        # Strategy 4: External anchor tag heuristic
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("http") and "linkedin.com" not in href:
                if any(kw in href.lower() for kw in ["apply", "careers", "jobs", "greenhouse", "lever", "workday"]):
                    return href, False

        # Strategy 5: Easy Apply Detection
        easy_apply = bool(soup.find(string=re.compile(r"Easy Apply", re.I)))

        # Graceful fallback: return None (caller retains original LinkedIn URL)
        return None, easy_apply
