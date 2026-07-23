"""
Industry Classifier

Pluggable abstraction and rule-based classifier for categorizing companies into industry sectors.
"""

from abc import ABC, abstractmethod
import re
from typing import List, Dict, Optional

# Taxonomy mapping keywords to industry sectors
INDUSTRY_RULES: Dict[str, List[str]] = {
    "Fintech & Payments": [
        "fintech", "payment", "banking", "finance", "crypto", "blockchain",
        "lending", "wallet", "stripe", "plaid", "payroll"
    ],
    "AI & Machine Learning": [
        "ai", "artificial intelligence", "machine learning", "deep learning",
        "llm", "nlp", "computer vision", "openai", "neural"
    ],
    "Developer Tools & Cloud": [
        "developer tools", "cloud", "infrastructure", "devops", "api",
        "database", "saas", "hasura", "docker", "kubernetes"
    ],
    "E-Commerce & Retail": [
        "e-commerce", "ecommerce", "retail", "marketplace", "shopping",
        "store", "logistics", "supply chain"
    ],
    "Healthcare & Biotech": [
        "health", "healthcare", "biotech", "medical", "telehealth", "pharma"
    ],
    "Cybersecurity": [
        "security", "cybersecurity", "auth", "identity", "threat", "encryption"
    ]
}


class BaseIndustryClassifier(ABC):
    """
    Abstract Base Class for Industry Classification.
    """

    @abstractmethod
    def classify(self, text: str, default: str = "Technology") -> str:
        """
        Classifies input text into a primary industry sector string.
        """
        pass


class RuleBasedIndustryClassifier(BaseIndustryClassifier):
    """
    Rule-based Industry Classifier matching keyword taxonomies.
    """

    def classify(self, text: str, default: str = "Technology") -> str:
        if not text:
            return default

        clean_text = text.lower()
        scores: Dict[str, int] = {}

        for industry, keywords in INDUSTRY_RULES.items():
            score = 0
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', clean_text):
                    score += 1
            if score > 0:
                scores[industry] = score

        if not scores:
            return default

        sorted_industries = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_industries[0][0]
