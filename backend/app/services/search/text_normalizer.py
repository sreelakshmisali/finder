"""
Text Normalizer Service

Normalizes job titles, descriptions, and query terms into canonical tokens.
Ensures comparisons happen on standardized representations (e.g., 'front end' -> 'frontend', 'js' -> 'javascript').
"""

import re
from typing import Set, List

# Dictionary of canonical replacements
SYNONYM_MAP = {
    "front end": "frontend",
    "front-end": "frontend",
    "back end": "backend",
    "back-end": "backend",
    "full stack": "fullstack",
    "full-stack": "fullstack",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "sr": "senior",
    "sr.": "senior",
    "jr": "junior",
    "jr.": "junior",
    "sw engineer": "software engineer",
    "soft engineer": "software engineer",
    "dev": "developer",
    "mgr": "manager",
    "admin": "administrative",
    "partner": "business partner",
}


class TextNormalizer:
    """
    Utility for canonicalizing job search text and tokens.
    """

    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Normalizes input text by lowercasing, stripping punctuation, and canonicalizing synonyms.
        """
        if not text:
            return ""

        result = text.lower()

        # Apply multi-word synonym replacements first
        for phrase, canonical in SYNONYM_MAP.items():
            if " " in phrase or "-" in phrase:
                result = re.sub(r'\b' + re.escape(phrase) + r'\b', canonical, result)

        # Replace hyphens with spaces for tokenization
        result = result.replace("-", " ")

        # Tokenize single words
        tokens = re.findall(r'[\w\.\+\#]+', result)
        normalized_tokens = []

        for token in tokens:
            if token in SYNONYM_MAP:
                normalized_tokens.append(SYNONYM_MAP[token])
            else:
                normalized_tokens.append(token)

        return " ".join(normalized_tokens)

    @classmethod
    def tokenize_normalized(cls, text: str) -> Set[str]:
        """
        Returns set of normalized tokens from input text.
        """
        norm_str = cls.normalize(text)
        return set(re.findall(r'[\w\.\+\#]+', norm_str))
