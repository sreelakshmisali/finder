from app.services.dedup.models import DuplicateResult
from app.services.dedup.engine import SimilarityEngine, SequenceMatcherEngine
from app.services.dedup.service import DuplicateDetectionService

__all__ = [
    "DuplicateResult",
    "SimilarityEngine",
    "SequenceMatcherEngine",
    "DuplicateDetectionService"
]
