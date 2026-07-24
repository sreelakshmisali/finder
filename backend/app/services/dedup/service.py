import re
import logging
from typing import List, Optional

from app.schemas.job import NormalizedJob
from app.models.job import Job
from app.core.config import get_settings
from app.services.dedup.models import DuplicateResult
from app.services.dedup.engine import SimilarityEngine, SequenceMatcherEngine

logger = logging.getLogger(__name__)

class DuplicateDetectionService:
    """
    Service responsible for determining if a job is a duplicate of existing jobs.
    Uses configurable weights and thresholds alongside a SimilarityEngine.
    """
    def __init__(self, engine: Optional[SimilarityEngine] = None):
        self.settings = get_settings()
        self.engine = engine or SequenceMatcherEngine()
        
    def normalize_string(self, text: str) -> str:
        """
        Normalizes a string for better similarity comparison.
        - Lowercase
        - Remove punctuation
        - Collapse multiple spaces
        - Trim whitespace
        """
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r"[^\w\s]", "", text)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def compare(self, job_new: NormalizedJob, job_existing: Job) -> DuplicateResult:
        """
        Compares a newly fetched job against an existing database job.
        Returns a DuplicateResult with detailed scores.
        """
        # Exact URL match bypasses similarity
        if job_new.url == job_existing.url:
            return DuplicateResult(
                is_duplicate=True,
                score=1.0,
                matched_fields={"url": 1.0},
                duplicate_of_id=job_existing.id
            )

        norm_company_new = self.normalize_string(job_new.company)
        norm_company_exist = self.normalize_string(job_existing.company)
        company_score = self.engine.calculate_similarity(norm_company_new, norm_company_exist)

        norm_title_new = self.normalize_string(job_new.title)
        norm_title_exist = self.normalize_string(job_existing.title)
        title_score = self.engine.calculate_similarity(norm_title_new, norm_title_exist)

        norm_loc_new = self.normalize_string(job_new.location)
        norm_loc_exist = self.normalize_string(job_existing.location)
        loc_score = self.engine.calculate_similarity(norm_loc_new, norm_loc_exist)

        # Truncate description for speed and avoid penalizing if one is much longer
        desc_new = self.normalize_string(job_new.description)[:1000]
        desc_exist = self.normalize_string(job_existing.description)[:1000]
        desc_score = self.engine.calculate_similarity(desc_new, desc_exist)
        
        # Calculate weighted score
        total_score = (
            (company_score * self.settings.DEDUP_COMPANY_WEIGHT) +
            (title_score * self.settings.DEDUP_TITLE_WEIGHT) +
            (loc_score * self.settings.DEDUP_LOCATION_WEIGHT) +
            (desc_score * self.settings.DEDUP_DESCRIPTION_WEIGHT)
        )
        
        # Ensure total weight sums to 1.0 if not perfectly configured
        weight_sum = (
            self.settings.DEDUP_COMPANY_WEIGHT +
            self.settings.DEDUP_TITLE_WEIGHT +
            self.settings.DEDUP_LOCATION_WEIGHT +
            self.settings.DEDUP_DESCRIPTION_WEIGHT
        )
        if weight_sum > 0:
            total_score = total_score / weight_sum

        is_dup = total_score >= self.settings.DEDUP_MIN_SCORE_THRESHOLD

        # If Company and Title are very high matches, we could bypass description penalty,
        # but the weighted sum approach already handles this gracefully if weights are tuned.
        
        matched_fields = {
            "company": company_score,
            "title": title_score,
            "location": loc_score,
            "description": desc_score,
        }
        
        if is_dup:
            logger.info(f"Duplicate detected (Score: {total_score:.2f}): '{job_new.title}' at '{job_new.company}' matches ID {job_existing.id}")

        return DuplicateResult(
            is_duplicate=is_dup,
            score=total_score,
            matched_fields=matched_fields,
            duplicate_of_id=job_existing.id if is_dup else None
        )

    def detect_duplicate(self, job_new: NormalizedJob, candidates: List[Job]) -> DuplicateResult:
        """
        Runs comparison against multiple candidates and returns the best match.
        """
        best_match = DuplicateResult(is_duplicate=False, score=0.0, matched_fields={})
        
        for candidate in candidates:
            result = self.compare(job_new, candidate)
            if result.is_duplicate and result.score > best_match.score:
                best_match = result
                
        return best_match
