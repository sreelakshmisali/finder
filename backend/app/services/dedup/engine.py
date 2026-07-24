from abc import ABC, abstractmethod
import difflib

class SimilarityEngine(ABC):
    """
    Abstract base class for text similarity engines.
    """
    @abstractmethod
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity score between two strings.
        Returns a float between 0.0 and 1.0.
        """
        pass

class SequenceMatcherEngine(SimilarityEngine):
    """
    Initial similarity engine using Python's built-in difflib.SequenceMatcher.
    """
    def calculate_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        return difflib.SequenceMatcher(None, text1, text2).ratio()
