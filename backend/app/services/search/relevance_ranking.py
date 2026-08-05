"""
Relevance Ranking Service (Intent Matching Engine)

Serves as the single source of truth for job search relevance across Finder.
Evaluates NormalizedJobs against SearchContext using intent-driven weighted scoring,
multi-domain RoleIntent extraction, domain conflict detection, and structured RoleExplanation diagnostics.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set
import re

from app.schemas.job import NormalizedJob
from app.core.config import settings
from app.services.search.query_intent_parser import SearchContext, SearchIntent, QueryIntentParser
from app.services.search.text_normalizer import TextNormalizer
from app.services.search.role_intent_extractor import RoleIntentExtractor, RoleIntent
from app.services.search.tech_taxonomy import DOMAIN_KEYWORDS, TECH_TO_DOMAINS

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
class RoleExplanation:
    """Explainable diagnostic decision object for ranking decisions."""
    matched_domains: List[str] = field(default_factory=list)
    conflicting_domains: List[str] = field(default_factory=list)
    matched_technologies: List[str] = field(default_factory=list)
    missing_technologies: List[str] = field(default_factory=list)
    role_similarity: float = 0.0
    confidence: float = 0.0
    decision: str = "rejected"


@dataclass
class RelevanceResult:
    """Structured diagnostic result for a scored job."""
    score: JobScore
    accepted: bool
    explanation: RoleExplanation
    matched_terms: List[str] = field(default_factory=list)
    missing_terms: List[str] = field(default_factory=list)
    penalties: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)


# Domain mismatch penalty rules
NON_TECH_DOMAINS = {"admin", "sales", "hr"}
ENGINEERING_DOMAINS = {"frontend", "backend", "fullstack", "data", "devops", "mobile"}


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
        Scores a single NormalizedJob against SearchContext using internal RoleIntent extraction and normalization.
        """
        raw_query = context.raw_query.strip()
        if not raw_query:
            score_obj = JobScore(total=50.0, confidence=1.0, breakdown=ScoreBreakdown(title=50.0))
            explanation = RoleExplanation(decision="accepted", confidence=1.0, role_similarity=1.0)
            return RelevanceResult(score=score_obj, accepted=True, explanation=explanation, reasons=["Empty query fallback match"])

        intent = context.intent

        # Extract Job RoleIntent
        job_intent: RoleIntent = RoleIntentExtractor.extract(job.title, job.description, job.required_skills)

        # 1. Normalize job text internally
        norm_title = TextNormalizer.normalize(job.title)
        norm_desc = TextNormalizer.normalize(job.description or "")
        title_tokens = set(re.findall(r'[\w\.\+\#\_]+', norm_title))
        q_tokens = set(re.findall(r'[\w\.\+\#\_]+', TextNormalizer.normalize(raw_query)))

        matched_terms: List[str] = []
        missing_terms: List[str] = []
        penalties: List[str] = []
        reasons: List[str] = []

        query_domains = set([d.name for d in intent.domains])
        query_techs = set([t.name.lower() for t in intent.technologies])

        # Calculate domain intersection and conflicts
        matched_domains = list(query_domains.intersection(job_intent.domains))
        conflicting_domains = list(job_intent.domains - query_domains) if query_domains else []

        # Determine Role Similarity Weight
        role_similarity = 0.50
        if query_domains and matched_domains:
            role_similarity = 1.0 if (job_intent.specialization and job_intent.specialization.lower() in raw_query.lower()) else 0.85
        elif job_intent.is_generic:
            role_similarity = 0.70  # Generic Software Engineer
        elif query_domains and conflicting_domains and not matched_domains:
            # Domain conflict (e.g. Frontend vs Game or Admin)
            if any(d in {"game", "admin", "sales", "hr"} for d in conflicting_domains):
                role_similarity = 0.15

        # --- FEATURE 1: TITLE SCORE (Weighted) ---
        title_pts = 0.0

        # Exact title query match
        if TextNormalizer.normalize(raw_query) in norm_title:
            title_pts += 100.0
            reasons.append("+ Exact title query match: +100")
            matched_terms.append(raw_query)
        else:
            # Technology matches in title
            tech_matched = False
            for tech_term in intent.technologies:
                norm_t = TextNormalizer.normalize(tech_term.name)
                if norm_t in norm_title or norm_t in title_tokens:
                    title_pts += 45.0
                    matched_terms.append(tech_term.name)
                    reasons.append(f"+ Technology '{tech_term.name}' in title: +45")
                    tech_matched = True

            # Domain concept matches in title
            if matched_domains:
                title_pts += 35.0
                reasons.append(f"+ Matched domains {matched_domains} in title: +35")

            # Role word match in title
            role_matched = False
            for role_term in intent.roles:
                if role_term.lower() in title_tokens:
                    role_matched = True
                    matched_terms.append(role_term.name)

            if role_matched:
                bonus = 30.0 * role_similarity
                title_pts += bonus
                reasons.append(f"+ Role matched in title (similarity {role_similarity:.2f}): +{bonus:.1f}")

        title_pts = min(title_pts, 100.0)

        # --- FEATURE 2: SKILLS SCORE (Weighted) ---
        skills_pts = 0.0
        job_skills = [TextNormalizer.normalize(s) for s in (job.required_skills or [])]
        matched_techs = []
        for tech_term in intent.technologies:
            norm_t = TextNormalizer.normalize(tech_term.name)
            if any(norm_t in sk for sk in job_skills):
                skills_pts += 50.0
                matched_terms.append(tech_term.name)
                matched_techs.append(tech_term.name)
                reasons.append(f"+ Required skill match for '{tech_term.name}': +50")

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

        # --- FEATURE 5: DOMAIN CONFLICT PENALTIES ---
        penalty_pts = 0.0

        query_is_tech = any(d in ENGINEERING_DOMAINS for d in query_domains) or \
                         any(t in q_tokens for t in ["developer", "engineer", "react", "python", "node", "java", "code"])

        # Check non-tech role title penalty
        if query_is_tech and any(d in NON_TECH_DOMAINS for d in job_intent.domains):
            penalty_pts -= 80.0
            penalty_msg = f"- Domain mismatch: Non-tech job domain '{job_intent.domains}' for tech query"
            penalties.append(penalty_msg)
            reasons.append(penalty_msg)

        # Check domain conflict penalty (e.g. Game/Mobile/Admin/Sales vs Web Frontend)
        if query_domains and conflicting_domains and not matched_domains and not job_intent.is_generic:
            penalty_pts -= 70.0
            penalty_msg = f"- Specialization conflict: Domain '{conflicting_domains}' conflicts with query domain '{query_domains}'"
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

        missing_techs = [t for t in query_techs if t not in matched_techs]

        explanation = RoleExplanation(
            matched_domains=matched_domains,
            conflicting_domains=conflicting_domains,
            matched_technologies=matched_techs,
            missing_technologies=missing_techs,
            role_similarity=round(role_similarity, 2),
            confidence=score_obj.confidence,
            decision="accepted" if accepted else "rejected"
        )

        job.relevance_score = score_obj.total
        job.match_reasons = reasons

        return RelevanceResult(
            score=score_obj,
            accepted=accepted,
            explanation=explanation,
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
                    f"Final: {result.score.total} | Decision: {result.explanation.decision.upper()} | "
                    f"Matched Domains: {result.explanation.matched_domains} | "
                    f"Conflicting Domains: {result.explanation.conflicting_domains}"
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
