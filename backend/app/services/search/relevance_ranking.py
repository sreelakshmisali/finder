"""
Relevance Ranking Service

Scores NormalizedJobs against the user's intent to filter out irrelevant jobs post-extraction.
Supports multiple ranker implementations (Keyword, Semantic, Hybrid).
"""

from typing import List, Tuple
import re

from app.schemas.job import NormalizedJob

class BaseRanker:
    """Abstract base class for all job rankers."""
    def rank(self, jobs: List[NormalizedJob], query: str, location: str = "") -> List[NormalizedJob]:
        raise NotImplementedError

class KeywordRanker(BaseRanker):
    """
    MVP keyword-based ranker using heuristics for positive/negative signals.
    """
    
    def rank(self, jobs: List[NormalizedJob], query: str, location: str = "") -> List[NormalizedJob]:
        scored_jobs = []
        q_tokens = set(re.findall(r'\w+', query.lower()))
        
        # Determine some basic intent
        is_frontend = "frontend" in q_tokens or "react" in q_tokens or "angular" in q_tokens or "vue" in q_tokens
        is_backend = "backend" in q_tokens or "python" in q_tokens or "java" in q_tokens or "node" in q_tokens
        is_data = "data" in q_tokens or "machine" in q_tokens or "ai" in q_tokens
        
        for job in jobs:
            score = 0
            reasons = []
            
            title_lower = job.title.lower()
            desc_lower = job.description.lower()
            
            # --- POSITIVE SIGNALS ---
            # Title match (exact or highly similar)
            title_tokens = set(re.findall(r'\w+', title_lower))
            match_count = len(q_tokens.intersection(title_tokens))
            if match_count > 0:
                bonus = match_count * 20
                score += bonus
                reasons.append(f"+ Title match ({match_count} words): +{bonus}")
                
            # Exact title match (extremely strong signal)
            if query.lower() in title_lower:
                score += 40
                reasons.append(f"+ Exact title match: +40")
                
            # Skills match
            skills_found = [sk for sk in job.required_skills if sk.lower() in q_tokens]
            if skills_found:
                bonus = len(skills_found) * 15
                score += bonus
                reasons.append(f"+ Skills found {skills_found}: +{bonus}")
            else:
                # Fallback to searching description for query tokens
                desc_hits = [t for t in q_tokens if t in desc_lower]
                if desc_hits:
                    bonus = len(desc_hits) * 5
                    score += bonus
                    reasons.append(f"+ Description keywords {desc_hits}: +{bonus}")
                    
            # Location match
            if location and location.lower() != "remote":
                if location.lower() in job.location.lower():
                    score += 15
                    reasons.append(f"+ Location match ({location}): +15")
            elif location and location.lower() == "remote" and job.remote:
                score += 15
                reasons.append(f"+ Remote match: +15")

            # --- NEGATIVE SIGNALS ---
            # Unrelated Department / Job Type
            if is_frontend and ("backend" in title_lower or "data engineer" in title_lower):
                score -= 30
                reasons.append("- Unrelated department (Backend/Data instead of Frontend): -30")
            elif is_backend and ("frontend" in title_lower or "react" in title_lower):
                score -= 30
                reasons.append("- Unrelated department (Frontend instead of Backend): -30")
            
            # Non-tech roles if searching tech
            non_tech = ["hr ", "human resources", "finance", "marketing", "sales", "account executive", "recruiter"]
            if any(nt in title_lower for nt in non_tech):
                score -= 50
                reasons.append("- Unrelated department (Non-tech role): -50")
                
            # Seniority mismatch
            if "junior" in q_tokens and ("senior" in title_lower or "staff" in title_lower or "principal" in title_lower):
                score -= 15
                reasons.append("- Seniority mismatch (Senior/Staff instead of Junior): -15")
            elif "senior" in q_tokens and ("junior" in title_lower or "intern" in title_lower):
                score -= 15
                reasons.append("- Seniority mismatch (Junior/Intern instead of Senior): -15")
                
            job.relevance_score = score
            job.match_reasons = reasons
            scored_jobs.append(job)
            
        # Sort descending by score
        return sorted(scored_jobs, key=lambda j: j.relevance_score or 0, reverse=True)


class RelevanceRankingService:
    """
    Entry point for ranking and filtering.
    """
    def __init__(self, ranker: BaseRanker = None):
        self.ranker = ranker or KeywordRanker()
        
    def rank_and_filter(
        self, 
        jobs: List[NormalizedJob], 
        query: str, 
        location: str = "", 
        min_score: int = 50
    ) -> Tuple[List[NormalizedJob], List[NormalizedJob]]:
        """
        Ranks jobs and splits them into accepted and rejected lists based on min_score.
        """
        if not jobs:
            return [], []
            
        ranked = self.ranker.rank(jobs, query, location)
        
        accepted = []
        rejected = []
        for job in ranked:
            if (job.relevance_score or 0) >= min_score:
                accepted.append(job)
            else:
                rejected.append(job)
                
        return accepted, rejected
