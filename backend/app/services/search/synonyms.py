"""
Role Synonym Registry

A static dictionary for expanding roles into multiple semantic variants to cast a wider net
during job search discovery. Future versions can be backed by a database or AI service.
"""

from typing import List, Dict

class RoleSynonymRegistry:
    """
    Registry for role synonyms and query expansion strategies.
    """

    # MVP Static Dictionary mapping a broad role to its search variants
    _REGISTRY: Dict[str, List[str]] = {
        "react developer": [
            "frontend developer",
            "react engineer",
            "react js developer",
            "frontend react engineer"
        ],
        "python developer": [
            "python engineer",
            "backend python developer",
            "python software engineer"
        ],
        "data scientist": [
            "machine learning engineer",
            "data analyst",
            "ai engineer",
            "applied scientist"
        ],
        # Add more defaults as needed
    }

    @classmethod
    def expand_role(cls, raw_query: str) -> List[str]:
        """
        Expands a raw query into multiple synonyms.
        Always includes the original query.
        """
        query_lower = raw_query.strip().lower()
        expanded = [raw_query.strip()]

        # Check for exact matches
        if query_lower in cls._REGISTRY:
            expanded.extend(cls._REGISTRY[query_lower])
            return list(dict.fromkeys(expanded))  # deduplicate preserving order

        # Check for partial matches (e.g. user typed "senior react developer")
        for key, synonyms in cls._REGISTRY.items():
            if key in query_lower:
                expanded.extend(synonyms)
                # Keep expanding or break? Let's break after first match for simplicity
                break

        return list(dict.fromkeys(expanded))
