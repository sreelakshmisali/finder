"""
Job Page Classifier Service

Evaluates a webpage to determine if it is a specific job posting, career index page,
company page, or irrelevant. Acts as a gatekeeper for the job extraction pipeline.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging
from bs4 import BeautifulSoup

from app.schemas.classification import PageType, ClassificationResult
from app.services.classification.signals import (
    ClassificationSignal,
    ApplyButtonSignal,
    JobTitleSignal,
    RequirementsSectionSignal,
    EmploymentKeywordsSignal,
    LocationSignal,
    MultipleJobsSignal,
    NegativeKeywordsSignal
)

logger = logging.getLogger(__name__)


class BasePageClassifier(ABC):
    """
    Abstract interface for classifying web pages in the job pipeline.
    """
    @abstractmethod
    def classify(self, url: str, html: str) -> ClassificationResult:
        pass


class RuleBasedJobPageClassifier(BasePageClassifier):
    """
    Rule-based classifier evaluating multiple signals to determine PageType.
    """
    def __init__(self, signals: Optional[List[ClassificationSignal]] = None, threshold: float = 0.5):
        self.signals = signals or [
            ApplyButtonSignal(),
            JobTitleSignal(),
            RequirementsSectionSignal(),
            EmploymentKeywordsSignal(),
            LocationSignal(),
            MultipleJobsSignal(),
            NegativeKeywordsSignal()
        ]
        self.threshold = threshold

    def classify(self, url: str, html: str) -> ClassificationResult:
        if not html:
            return ClassificationResult(
                page_type=PageType.IRRELEVANT,
                confidence=1.0,
                matched_signals=[],
                failed_signals=[],
                is_valid_job=False,
                rejected_reason="Empty HTML content"
            )

        soup = BeautifulSoup(html, "html.parser")
        
        matched_signals = []
        failed_signals = []
        total_score = 0.0
        max_possible_score = sum(s.weight for s in self.signals if s.weight > 0)

        for signal in self.signals:
            matched = signal.evaluate(url, html, soup)
            if matched:
                matched_signals.append(signal.name)
                total_score += signal.weight
            else:
                failed_signals.append(signal.name)

        # Normalize score between 0.0 and 1.0 (clamped)
        confidence = max(0.0, min(1.0, total_score / max_possible_score)) if max_possible_score > 0 else 0.0

        # Determine PageType based on signals
        page_type = PageType.IRRELEVANT
        rejected_reason = None

        if "negative_keywords" in matched_signals:
            page_type = PageType.IRRELEVANT
            rejected_reason = "Negative signals dominant (blog/news/login)"
            confidence = 1.0  # Highly confident it's irrelevant
        elif "multiple_jobs_index" in matched_signals and "apply_button" not in matched_signals:
            page_type = PageType.CAREER_PAGE
            rejected_reason = "Identified as Career Index page"
        elif total_score > 0 and confidence >= self.threshold:
            page_type = PageType.JOB_POSTING
        elif total_score > 0:
            page_type = PageType.COMPANY_PAGE
            rejected_reason = f"Score below threshold ({confidence:.2f} < {self.threshold:.2f})"
        else:
            rejected_reason = "No positive signals matched"

        is_valid_job = (page_type == PageType.JOB_POSTING) and (confidence >= self.threshold)

        result = ClassificationResult(
            page_type=page_type,
            confidence=confidence,
            matched_signals=matched_signals,
            failed_signals=failed_signals,
            is_valid_job=is_valid_job,
            rejected_reason=rejected_reason
        )

        logger.debug(f"Classified '{url}' as {page_type.value} (Valid: {is_valid_job}, Conf: {confidence:.2f})")
        return result
