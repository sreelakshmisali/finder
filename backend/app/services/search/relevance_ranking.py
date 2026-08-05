"""
Relevance Ranking Service (Intent Matching Engine)

Serves as the single source of truth for job search relevance across Finder.
Evaluates NormalizedJobs against SearchContext using intent-driven weighted scoring,
text normalization, domain mismatch penalties, and structured diagnostics.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import re

from app.schemas.job import NormalizedJob
from app.core.config import settings
from app.services.search.query_intent_parser import SearchContext, SearchIntent, QueryIntentParser, DOMAIN_DICTIONARY
from app.services.search.text_normalizer import TextNormalizer

logger = logging.getLogger(__name__)


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown per feature category."""
    title: float = 0.0
    skills: float = 0.0
    description: float = 0.0
    location: float = 0.0
    penalties: float = 0.0


@dataclass
class JobScore:
    """Encapsulates total score, confidence, and category breakdown."""
    total: float
    confidence: float
    breakdown: ScoreBreakdown


@dataclass
class RelevanceResult:
    """Structured diagnostic result for a scored job."""
    score: JobScore
    accepted: bool
    matched_terms: List[str] = field(default_factory=list)
    missing_terms: List[str] = field(default_factory=list)
    penalties: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)


# Domain mismatch penalty rules
NON_TECH_ROLES = {"administrative", "admin", "business partner", "account manager", "account executive", "hr", "recruiter", "finance", "sales"}
ENGINEERING_DOMAINS = {"frontend", "backend", "fullstack", "data", "devops", "software"}


class RelevanceRankingService:
    """
    Centralized Intent Matching Engine.
    Executes scoring, ranking, and filtering pipeline: score() → rank() → filter().
    """

    def __init__(
        self,
        weight_title: Optional[float] = None,
        weight_skills: Optional[float] = None,
        weight_desc: Optional[float] = None,
        weight_loc: Optional[float] = None
    ):
        self.w_title = weight_title if weight_title is not None else getattr(settings, "RANKING_WEIGHT_TITLE", 0.60)
        self.w_skills = weight_skills if weight_skills is not None else getattr(settings, "RANKING_WEIGHT_SKILLS", 0.25)
        self.w_desc = weight_desc if weight_desc is not None else getattr(settings, "RANKING_WEIGHT_DESCRIPTION", 0.10)
        self.w_loc = weight_loc if weight_loc is not None else getattr(settings, "RANKING_WEIGHT_LOCATION", 0.05)

    def score_job(self, job: NormalizedJob, context: SearchContext) -> RelevanceResult:
        """
        Scores a single NormalizedJob against SearchContext using internal text normalization.
        """
        raw_query = context.raw_query.strip()
        if not raw_query:
            score_obj = JobScore(total=50.0, confidence=1.0, breakdown=ScoreBreakdown(title=50.0))
            return RelevanceResult(score=score_obj, accepted=True, reasons=["Empty query fallback match"])

        intent = context.intent

        # 1. Normalize job text internally
        norm_title = TextNormalizer.normalize(job.title)
        norm_desc = TextNormalizer.normalize(job.description or "")
        title_tokens = set(re.findall(r'[\w\.\+\#]+', norm_title))

        matched_terms: List[str] = []
        missing_terms: List[str] = []
        penalties: List[str] = []
        reasons: List[str] = []

        # --- FEATURE 1: TITLE SCORE (Weighted) ---
        title_pts = 0.0
        q_tokens = set(re.findall(r'[\w\.\+\#]+', TextNormalizer.normalize(raw_query)))

        # Exact title match
        if TextNormalizer.normalize(raw_query) in norm_title:
            title_pts += 100.0
            reasons.append("+ Exact title query match: +100")
            matched_terms.append(raw_query)

        # Query token overlap in title
        title_hits = q_tokens.intersection(title_tokens)
        if title_hits:
            title_pts += len(title_hits) * 30.0
            matched_terms.extend(list(title_hits))
            reasons.append(f"+ Title matched words {list(title_hits)}: +{len(title_hits) * 30}")

        # Technology matches in title
        for tech in intent.technologies:
            if tech.lower() in title_tokens or tech.lower() in norm_title:
                title_pts += 40.0
                matched_terms.append(tech.name)
                reasons.append(f"+ Technology '{tech.name}' in title: +40")

        # Domain concept matches in title
        for domain_term in intent.domains:
            d_name = domain_term.name.lower()
            d_keywords = DOMAIN_DICTIONARY.get(d_name, [d_name])
            if any(kw in norm_title for kw in d_keywords):
                title_pts += 35.0
                matched_terms.append(f"domain:{d_name}")
                reasons.append(f"+ Domain concept '{d_name}' matched in title: +35")

        # Role matches in title
        for role in intent.roles:
            if role.lower() in title_tokens:
                title_pts += 25.0
                matched_terms.append(role.name)
                reasons.append(f"+ Role '{role.name}' matched in title: +25")

        # Cap title points
        title_pts = min(title_pts, 100.0)

        # --- FEATURE 2: SKILLS SCORE (Weighted) ---
        skills_pts = 0.0
        job_skills = [TextNormalizer.normalize(s) for s in (job.required_skills or [])]
        for tech in intent.technologies:
            if any(tech.lower() in sk for sk in job_skills):
                skills_pts += 50.0
                matched_terms.append(tech.name)
                reasons.append(f"+ Required skill match for '{tech.name}': +50")

        skills_pts = min(skills_pts, 100.0)

        # --- FEATURE 3: DESCRIPTION SCORE (Weighted) ---
        desc_pts = 0.0
        for q_tok in q_tokens:
            if len(q_tok) > 1 and q_tok in norm_desc:
                desc_pts += 20.0
                if q_tok not in matched_terms:
                    matched_terms.append(q_tok)

        desc_pts = min(desc_pts, 100.0)

        # --- FEATURE 4: LOCATION SCORE (Weighted) ---
        loc_pts = 0.0
        if context.location and context.location.lower() != "remote":
            if context.location.lower() in job.location.lower():
                loc_pts += 100.0
                reasons.append(f"+ Location match '{context.location}': +100")
        elif context.remote_only and job.remote:
            loc_pts += 100.0
            reasons.append("+ Remote work match: +100")

        # --- FEATURE 5: DOMAIN MISMATCH PENALTIES ---
        penalty_pts = 0.0

        query_is_tech = any(d in ENGINEERING_DOMAINS for d in [dt.name for dt in intent.domains]) or \
                         any(t in q_tokens for t in ["developer", "engineer", "react", "python", "node", "java", "code"])

        is_non_tech_title = any(nt in norm_title for nt in NON_TECH_ROLES)

        if query_is_tech and is_non_tech_title:
            penalty_pts -= 80.0
            penalty_msg = f"- Domain mismatch: Non-tech title '{job.title}' for tech query"
            penalties.append(penalty_msg)
            reasons.append(penalty_msg)

        # Compute weighted total score
        raw_total = (
            (title_pts * self.w_title) +
            (skills_pts * self.w_skills) +
            (desc_pts * self.w_desc) +
            (loc_pts * self.w_loc) +
            penalty_pts
        )

        confidence = min(max((len(matched_terms) / max(len(q_tokens), 1)), 0.1), 1.0)
        breakdown = ScoreBreakdown(
            title=round(title_pts * self.w_title, 2),
            skills=round(skills_pts * self.w_skills, 2),
            description=round(desc_pts * self.w_desc, 2),
            location=round(loc_pts * self.w_loc, 2),
            penalties=round(penalty_pts, 2)
        )

        score_obj = JobScore(
            total=round(raw_total, 2),
            confidence=round(confidence, 2),
            breakdown=breakdown
        )

        accepted = (raw_total > 0) and (penalty_pts >= 0 or title_pts > 40)

        for q_tok in q_tokens:
            if q_tok not in matched_terms and len(q_tok) > 2:
                missing_terms.append(q_tok)

        job.relevance_score = score_obj.total
        job.match_reasons = reasons

        return RelevanceResult(
            score=score_obj,
            accepted=accepted,
            matched_terms=list(set(matched_terms)),
            missing_terms=list(set(missing_terms)),
            penalties=penalties,
            reasons=reasons
        )

    def score(self, jobs: List[NormalizedJob], context: SearchContext) -> List[Tuple[NormalizedJob, RelevanceResult]]:
        """
        Step 1: Score all candidate jobs.
        """
        return [(job, self.score_job(job, context)) for job in jobs]

    def rank(self, scored_items: List[Tuple[NormalizedJob, RelevanceResult]]) -> List[Tuple[NormalizedJob, RelevanceResult]]:
        """
        Step 2: Rank items descending by total relevance score.
        """
        return sorted(scored_items, key=lambda item: item[1].score.total, reverse=True)

    def filter(self, ranked_items: List[Tuple[NormalizedJob, RelevanceResult]]) -> Tuple[List[NormalizedJob], List[Tuple[NormalizedJob, RelevanceResult]]]:
        """
        Step 3: Filter accepted vs rejected items based on net evidence.
        """
        accepted: List[NormalizedJob] = []
        rejected: List[Tuple[NormalizedJob, RelevanceResult]] = []

        for job, result in ranked_items:
            if result.accepted:
                accepted.append(job)
            else:
                rejected.append((job, result))
                logger.info(
                    f"[IntentEngine] Title: '{job.title}' | Company: '{job.company}' | "
                    f"Final: {result.score.total} (Title: {result.score.breakdown.title}, Penalties: {result.score.breakdown.penalties}) → REJECTED"
                )

        return accepted, rejected

    def rank_and_filter(
        self,
        jobs: List[NormalizedJob],
        query: str,
        location: str = "",
        remote_only: bool = False
    ) -> Tuple[List[NormalizedJob], List[NormalizedJob]]:
        """
        Unified public API orchestrating: score() → rank() → filter().
        """
        if not jobs:
            return [], []

        context = QueryIntentParser.parse(query=query, location=location, remote_only=remote_only)
        scored = self.score(jobs, context)
        ranked = self.rank(scored)
        accepted_jobs, rejected_tuples = self.filter(ranked)

        logger.info(
            f"[IntentEngine] Evaluated {len(jobs)} candidate jobs for query '{query}' → "
            f"{len(accepted_jobs)} accepted, {len(rejected_tuples)} rejected."
        )

        rejected_jobs = [j for j, r in rejected_tuples]
        return accepted_jobs, rejected_jobs
