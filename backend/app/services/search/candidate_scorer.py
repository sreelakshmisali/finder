"""
Candidate URL Scorer

Scores candidate URLs before crawling to prioritize high-quality sources and ensure diversity.
"""

from typing import List, Dict, Tuple
from urllib.parse import urlparse

class CandidateScorer:
    """
    Scores candidate URLs based on ATS provider priority, URL structure, and search engine rank.
    """
    
    @staticmethod
    def score_urls(candidate_urls: List[str], target_role: str = "") -> List[Tuple[str, int]]:
        """
        Scores a list of candidate URLs and returns them sorted by score descending.
        Takes into account the original position in the list (assuming they came from a search engine,
        so earlier is higher ranked).
        """
        scored = []
        for idx, url in enumerate(candidate_urls):
            score = 50  # Base score
            
            parsed = urlparse(url.lower())
            netloc = parsed.netloc
            path = parsed.path
            
            # 1. ATS Provider Priority
            if "greenhouse.io" in netloc:
                score += 30
            elif "lever.co" in netloc:
                score += 25
            elif "ashbyhq.com" in netloc:
                score += 25
            elif "workdayjobs.com" in netloc or "smartrecruiters.com" in netloc:
                score += 20
            else:
                score += 5 # Unknown provider
                
            # 2. URL Structure
            if "/jobs" in path or "/job/" in path or "jobs." in netloc:
                score += 20
            elif "/careers" in path or "/career" in path or "careers." in netloc:
                score += 15
            elif "/blog" in path or "/news" in path:
                score -= 30
            elif "/docs" in path or "/help" in path or "/support" in path:
                score -= 50
                
            # 3. Search Engine Rank
            if idx == 0:
                score += 20
            elif 1 <= idx <= 4:
                score += 10
            elif 5 <= idx <= 9:
                score += 5
                
            # 4. Query Similarity (simple keyword check in URL)
            if target_role:
                keywords = target_role.lower().split()
                if any(kw in url.lower() for kw in keywords if len(kw) > 3):
                    score += 10
                    
            scored.append((url, score))
            
        # Sort by score descending
        return sorted(scored, key=lambda x: x[1], reverse=True)
