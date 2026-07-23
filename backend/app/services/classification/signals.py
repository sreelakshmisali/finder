"""
Classification Signals Rule Engine

Defines individual signal rules used to classify web pages.
"""

from abc import ABC, abstractmethod
import re
from bs4 import BeautifulSoup
from typing import Tuple


class ClassificationSignal(ABC):
    """
    Abstract rule for evaluating a specific classification signal on a webpage.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the signal for metadata reporting."""
        pass

    @property
    @abstractmethod
    def weight(self) -> float:
        """Score weight added (or subtracted) if signal matches."""
        pass

    @abstractmethod
    def evaluate(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        """
        Evaluates the signal against the parsed page.
        Returns True if the signal is present, False otherwise.
        """
        pass


class ApplyButtonSignal(ClassificationSignal):
    name = "apply_button"
    weight = 30.0

    def evaluate(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        apply_patterns = [
            re.compile(r'apply\s*(now|for this job)?', re.IGNORECASE),
            re.compile(r'submit\s*application', re.IGNORECASE)
        ]
        
        # Look for explicit links or buttons with apply text
        for tag in soup.find_all(['a', 'button']):
            text = tag.get_text(separator=' ', strip=True).lower()
            if any(p.match(text) for p in apply_patterns):
                return True
                
        # Look for typical ATS apply iframe or form IDs
        if soup.find('form', id=re.compile(r'(apply|application).*', re.IGNORECASE)):
            return True
        if soup.find('iframe', id=re.compile(r'grnhse_iframe', re.IGNORECASE)):
            return True

        return False


class JobTitleSignal(ClassificationSignal):
    name = "job_title"
    weight = 35.0

    def evaluate(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        # Check title tag or H1 for common job title keywords
        keywords = ["engineer", "developer", "manager", "designer", "director", "specialist", "associate"]
        
        title = soup.title.string if soup.title else ""
        h1s = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
        
        text_to_check = (title + " " + " ".join(h1s)).lower()
        
        # If it explicitly says "Careers" or "Jobs" alone, it might be a career index page, not a specific job title
        # But if it has a specific role keyword, it's strong.
        for kw in keywords:
            if kw in text_to_check:
                # To avoid confusing with a generic "Engineering Jobs" index page:
                if "jobs" not in text_to_check.replace("jobs at", ""):
                    return True
                    
        return False


class RequirementsSectionSignal(ClassificationSignal):
    name = "requirements"
    weight = 25.0

    def evaluate(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        headers = [h.get_text(strip=True).lower() for h in soup.find_all(['h2', 'h3', 'h4', 'strong', 'b'])]
        
        target_sections = [
            "requirements", "qualifications", "what you'll do", 
            "what you will do", "responsibilities", "who you are",
            "about the role", "your role"
        ]
        
        for h in headers:
            if any(target in h for target in target_sections):
                return True
        return False


class EmploymentKeywordsSignal(ClassificationSignal):
    name = "employment_keywords"
    weight = 20.0

    def evaluate(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        text = soup.get_text(separator=' ', strip=True).lower()
        
        keywords = ["full-time", "part-time", "salary", "benefits", "job type", "experience level", "401k", "equity"]
        matches = sum(1 for kw in keywords if kw in text)
        
        return matches >= 2  # Require at least 2 keywords to be reasonably confident


class LocationSignal(ClassificationSignal):
    name = "location"
    weight = 15.0

    def evaluate(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        text = soup.get_text(separator=' ', strip=True).lower()
        if "remote" in text or "hybrid" in text or "on-site" in text or "onsite" in text:
            return True
        # Specific locations could be checked, but remote/hybrid is very common in tech jobs
        return False


class MultipleJobsSignal(ClassificationSignal):
    name = "multiple_jobs_index"
    weight = -20.0  # Penalize JOB_POSTING score if it looks like an index

    def evaluate(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        # If the page has many links containing 'job' or 'role', it's likely a career page index
        job_links = 0
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            text = a.get_text(strip=True).lower()
            if "/job/" in href or "/careers/" in href or "view job" in text:
                job_links += 1
        
        return job_links >= 4


class NegativeKeywordsSignal(ClassificationSignal):
    name = "negative_keywords"
    weight = -40.0

    def evaluate(self, url: str, html: str, soup: BeautifulSoup) -> bool:
        title = (soup.title.string if soup.title else "").lower()
        h1s = " ".join([h1.get_text(strip=True) for h1 in soup.find_all('h1')]).lower()
        
        header_text = title + " " + h1s
        
        negatives = [
            "blog", "news", "press release", "privacy policy", 
            "terms of service", "cookie notice", "redirect", 
            "page not found", "404", "login", "sign in"
        ]
        
        return any(neg in header_text for neg in negatives)
