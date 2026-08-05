"""
Relevance Ranking Service (Intent Matching Engine)

Serves as the single source of truth for job search relevance across Finder.
Evaluates NormalizedJobs against SearchContext by comparing SearchIntent against RoleIntent
extracted via RoleIntentExtractor, computing multi-domain intersection, role similarity,
and structured RoleExplanation diagnostics.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set
import re

from app.schemas.job import NormalizedJob
from app.core.config import settings
from app.services.search.query_intent_parser import SearchContext, SearchIntent, QueryIntentParser
from app.services.search.text_normalizer import TextNormalizer
from app.services.search.role_intent_extractor import RoleIntentExtractor, RoleIntent, is_tech_match
from app.services.search.tech_taxonomy import DOMAIN_TITLE_TRIGGERS

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
    """Structured explainability object for ranking decisions."""
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


NON_TECH_DOMAINS = {"admin", "sales", "hr", "finance"}


class RelevanceRankingService:
    """
    Centralized Intent Matching Engine comparing SearchIntent against RoleIntent.
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
        Scores a single NormalizedJob by comparing SearchContext intent against job RoleIntent.
        """
        raw_query = context.raw_query.strip()
        if not raw_query:
            score_obj = JobScore(total=50.0, confidence=1.0, breakdown=ScoreBreakdown(title=50.0))
            exp = RoleExplanation(decision="accepted", confidence=1.0, role_similarity=1.0)
            return RelevanceResult(score=score_obj, accepted=True, explanation=exp, reasons=["Empty query fallback match"])

        intent = context.intent

        # 1. Extract RoleIntent for Candidate Job
        role_intent: RoleIntent = RoleIntentExtractor.extract(job.title, job.description, job.required_skills)

        # 2. Text Normalization
        norm_title = TextNormalizer.normalize(job.title)
        norm_desc = TextNormalizer.normalize(job.description or "")
        title_tokens = set(re.findall(r'[\w\.\+\#]+', norm_title))
        q_norm = TextNormalizer.normalize(raw_query)
        q_tokens = set(re.findall(r'[\w\.\+\#]+', q_norm))

        matched_terms: List[str] = []
        missing_terms: List[str] = []
        penalties: List[str] = []
        reasons: List[str] = []

        query_domains = {d.name.lower() for d in intent.domains}
        query_techs = {t.name.lower() for t in intent.technologies}

        # Multi-domain intersection
        job_domains = role_intent.domains
        matched_domains_set = query_domains.intersection(job_domains)
        conflicting_domains_set = (job_domains - query_domains) if (query_domains and not matched_domains_set and not role_intent.is_generic) else set()

        matched_domains = sorted(list(matched_domains_set))
        conflicting_domains = sorted(list(conflicting_domains_set))

        matched_techs: List[str] = []
        missing_techs: List[str] = []

        for q_tech in query_techs:
            tech_norm = TextNormalizer.normalize(q_tech)
            in_t = is_tech_match(tech_norm, norm_title)
            in_d = is_tech_match(tech_norm, norm_desc)
            in_s = any(is_tech_match(tech_norm, TextNormalizer.normalize(s)) for s in (job.required_skills or []))

            if in_t or in_s or in_d:
                matched_techs.append(q_tech)
                matched_terms.append(q_tech)
            else:
                missing_techs.append(q_tech)

        # --- ROLE SIMILARITY & TITLE SCORE ---
        role_sim = 0.0
        title_pts = 0.0

        if q_norm in norm_title:
            role_sim = 1.0
            title_pts = 100.0
            reasons.append("+ Exact title query match: +100")
            matched_terms.append(raw_query)
        elif matched_domains_set:
            role_sim = 0.85
            title_pts = 85.0
            reasons.append(f"+ Domain intersection matched {matched_domains}: +85")
        elif role_intent.is_generic and matched_techs:
            role_sim = 0.70
            title_pts = 70.0
            reasons.append(f"+ Generic software title with matching technologies {matched_techs}: +70")
        elif conflicting_domains_set:
            role_sim = 0.15
            title_pts = 15.0
            reasons.append(f"- Conflicting specialization domains {conflicting_domains}: +15 baseline title score")
        else:
            # Baseline token overlap
            title_hits = q_tokens.intersection(title_tokens)
            if title_hits:
                role_sim = 0.40
                title_pts = 40.0
                matched_terms.extend(list(title_hits))
                reasons.append(f"+ Token overlap in title {list(title_hits)}: +40")

        title_pts = min(title_pts, 100.0)

        # --- FEATURE 2: SKILLS SCORE ---
        skills_pts = 0.0
        if matched_techs:
            skills_pts = len(matched_techs) * 50.0
            reasons.append(f"+ Tech skills matched {matched_techs}: +{skills_pts}")
        skills_pts = min(skills_pts, 100.0)

        # --- FEATURE 3: DESCRIPTION SCORE ---
        desc_pts = 0.0
        for q_tok in q_tokens:
            if len(q_tok) > 1 and is_tech_match(q_tok, norm_desc):
                desc_pts += 20.0
                if q_tok not in matched_terms:
                    matched_terms.append(q_tok)
        desc_pts = min(desc_pts, 100.0)

        # --- FEATURE 4: LOCATION SCORE ---
        loc_pts = 0.0
        if context.location and context.location.lower() != "remote":
            if context.location.lower() in job.location.lower():
                loc_pts = 100.0
                reasons.append(f"+ Location match '{context.location}': +100")
        elif context.remote_only and job.remote:
            loc_pts = 100.0
            reasons.append("+ Remote work match: +100")

        # --- FEATURE 5: DOMAIN CONFLICT PENALTIES ---
        penalty_pts = 0.0
        if conflicting_domains_set and not matched_domains_set and not role_intent.is_generic:
            penalty_pts -= 80.0
            penalty_msg = f"- Domain conflict: Candidate specialization {conflicting_domains} conflicts with query {query_domains}"
            penalties.append(penalty_msg)
            reasons.append(penalty_msg)

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

        # Acceptance Gate: positive score AND (no conflicting domains OR strong title match >= 0.85)
        accepted = (raw_total > 0) and (not conflicting_domains_set or role_sim >= 0.85)

        for q_tok in q_tokens:
            if q_tok not in matched_terms and len(q_tok) > 2:
                missing_terms.append(q_tok)

        explanation = RoleExplanation(
            matched_domains=matched_domains,
            conflicting_domains=conflicting_domains,
            matched_technologies=matched_techs,
            missing_technologies=missing_techs,
            role_similarity=round(role_sim, 2),
            confidence=round(confidence, 2),
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
        Step 3: Filter accepted vs rejected items.
        """
        accepted: List[NormalizedJob] = []
        rejected: List[Tuple[NormalizedJob, RelevanceResult]] = []

        for job, result in ranked_items:
            if result.accepted:
                accepted.append(job)
            else:
                rejected.append((job, result))
                exp = result.explanation
                logger.info(
                    f"[IntentEngine] Title: '{job.title}' | Company: '{job.company}' | "
                    f"Final Score: {result.score.total} | RoleSim: {exp.role_similarity} | "
                    f"Matched Domains: {exp.matched_domains} | Conflicting Domains: {exp.conflicting_domains} → REJECTED"
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
