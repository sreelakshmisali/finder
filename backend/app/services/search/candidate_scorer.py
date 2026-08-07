"""
Candidate URL Scorer

Scores candidate URLs before crawling to prioritize high-quality sources and ensure diversity.
"""

from typing import List, Tuple, Optional
from urllib.parse import urlparse

from app.core.scheduler_config import SchedulerConfig
from app.services.crawl.provider_classifier import ProviderClassifier


class CandidateScorer:
    """
    Scores candidate URLs based on ATS provider priority, URL structure, and search engine rank.
    """
    
    @staticmethod
    def score_urls(
        candidate_urls: List[str], 
        target_role: str = "",
        config: Optional[SchedulerConfig] = None
    ) -> List[Tuple[str, int, str]]:
        """
        Scores a list of candidate URLs and returns them sorted by score descending.
        Returns a list of tuples: (url, score, provider_tag).
        """
        cfg = config or SchedulerConfig.from_env()
        scored = []

        for idx, url in enumerate(candidate_urls):
            score = 50  # Base score
            
            prov_tag = ProviderClassifier.classify(url)
            prov_cfg = cfg.provider_priorities.get(prov_tag, cfg.provider_priorities["generic_board"])

            # 1. ATS / Provider Priority Bonus from SchedulerConfig
            priority_bonus = (10 - prov_cfg.priority) * 10
            score += priority_bonus
                
            # 2. URL Structure Signals
            parsed = urlparse(url.lower())
            netloc = parsed.netloc
            path = parsed.path

            if "/jobs" in path or "/job/" in path or "jobs." in netloc:
                score += 20
            elif "/careers" in path or "/career" in path or "careers." in netloc:
                score += 15
            elif "/blog" in path or "/news" in path:
                score -= 30
            elif "/docs" in path or "/help" in path or "/support" in path:
                score -= 50
                
            # 3. Search Engine Rank Bonus
            if idx == 0:
                score += 20
            elif 1 <= idx <= 4:
                score += 10
            elif 5 <= idx <= 9:
                score += 5
                
            # 4. Query Similarity
            if target_role:
                keywords = target_role.lower().split()
                if any(kw in url.lower() for kw in keywords if len(kw) > 3):
                    score += 10
                    
            scored.append((url, score, prov_tag))
            
        # Sort by score descending
        return sorted(scored, key=lambda x: x[1], reverse=True)
