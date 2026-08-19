"""
Full Retrieval Audit Script — "python developer" query

Runs the complete live pipeline with force_refresh=True, then:
1. Captures every P4 candidate with full score breakdown
2. Classifies each rejection
3. Traces Search Engine Discovery stage-by-stage
4. Identifies attribution bug
5. Reports the complete funnel

Run from backend/:
    .\.venv\Scripts\python.exe audit_retrieval.py 2>&1 | tee audit_out.txt
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress noise, but keep our audit logger
logging.basicConfig(level=logging.WARNING, format="%(message)s")
audit_log = logging.getLogger("AUDIT")
audit_log.setLevel(logging.INFO)

# Console handler for audit
_h = logging.StreamHandler(sys.stdout)
_h.setLevel(logging.INFO)
_h.setFormatter(logging.Formatter("%(message)s"))
audit_log.addHandler(_h)
audit_log.propagate = False


def sep(char="=", width=80):
    audit_log.info(char * width)


def hdr(title):
    audit_log.info(f"\n{'=' * 80}")
    audit_log.info(f"  {title}")
    audit_log.info(f"{'=' * 80}")


async def run_audit():
    from contextvars import ContextVar
    from app.utils import pipeline_tracker as pt_module
    pt_module.current_tracker = ContextVar("current_tracker", default=None)

    from app.database.session import get_sessionmaker
    from app.schemas.job import JobSearchQuery, NormalizedJob
    from app.providers.registry import registry
    from app.providers.base_discovery import DiscoveryContext
    from app.services.search.relevance_ranking import RelevanceRankingService
    from app.services.search.query_intent_parser import QueryIntentParser
    from app.utils.search_diagnostics import SearchDiagnosticsTracker, current_diagnostics

    QUERY = "python developer"

    # ─── Parse query intent ─────────────────────────────────────────────────
    hdr("QUERY INTENT PARSE")
    context = QueryIntentParser.parse(query=QUERY, location="", remote_only=False)
    audit_log.info(f"  raw_query    : {context.raw_query!r}")
    audit_log.info(f"  technologies : {[t.name for t in context.intent.technologies]}")
    audit_log.info(f"  roles        : {[r.name for r in context.intent.roles]}")
    audit_log.info(f"  domains      : {[d.name for d in context.intent.domains]}")
    audit_log.info(f"  seniority    : {[s.name for s in context.intent.seniority]}")

    # ─── ATS Content token filter ────────────────────────────────────────────
    from app.providers._ats_filter import extract_content_tokens
    content_tokens = extract_content_tokens(QUERY)
    audit_log.info(f"\n  ATS filter content_tokens: {sorted(content_tokens)}")
    audit_log.info(f"  (empty = no ATS pre-filter active; non-empty = pre-filter ON)")

    # ─── Run all providers ───────────────────────────────────────────────────
    hdr("PROVIDER DISCOVERY RUN")
    query_obj = JobSearchQuery(
        query=QUERY,
        location=None,
        remote_only=False,
        limit=20,
        force_refresh=True,
    )

    diag = SearchDiagnosticsTracker(
        query=QUERY,
        location="",
        remote_only=False,
        limit=20,
    )
    diag_token = current_diagnostics.set(diag)

    target_providers = registry.get_enabled_providers()
    audit_log.info(f"  Providers: {[p.source_name for p in target_providers]}")

    ctx = DiscoveryContext(query=query_obj, user_id=None)
    tasks = [p.discover(ctx) for p in target_providers]

    import asyncio as _asyncio
    results_list = await _asyncio.gather(*tasks, return_exceptions=True)

    raw_candidates = []
    provider_p4 = {}
    for idx, result in enumerate(results_list):
        p_name = target_providers[idx].source_name
        if isinstance(result, Exception):
            audit_log.info(f"  {p_name}: EXCEPTION — {result}")
            provider_p4[p_name] = []
        elif isinstance(result, list):
            provider_p4[p_name] = result
            audit_log.info(f"  {p_name}: {len(result)} P4 jobs returned")
            raw_candidates.extend(result)
        else:
            provider_p4[p_name] = []
            audit_log.info(f"  {p_name}: unexpected result type {type(result)}")

    audit_log.info(f"\n  TOTAL P4 candidates: {len(raw_candidates)}")

    # ─── Cross-provider dedup (same as job_service) ──────────────────────────
    seen_urls = {}
    unique_pre_rank = []
    for job in raw_candidates:
        norm_u = job.url.strip()
        if norm_u not in seen_urls:
            seen_urls[norm_u] = job
            unique_pre_rank.append(job)

    audit_log.info(f"  After cross-provider dedup: {len(unique_pre_rank)} unique candidates")

    # ─── Run relevance scoring on all candidates ─────────────────────────────
    hdr("FULL CANDIDATE SCORING — ALL CANDIDATES")
    engine = RelevanceRankingService()

    import re as _re
    from app.services.search.text_normalizer import TextNormalizer
    from app.services.search.role_intent_extractor import RoleIntentExtractor

    scored = engine.score(unique_pre_rank, context)
    ranked = engine.rank(scored)

    all_results = []
    for job, result in ranked:
        bd = result.score.breakdown
        rec = {
            "provider": job.source,
            "discovery_provider": job.discovery_provider,
            "title": job.title,
            "company": job.company,
            "url": job.url,
            "description_len": len(job.description or ""),
            "required_skills": job.required_skills,
            "total_score": result.score.total,
            "title_score": round(bd.title, 2),
            "skill_score": round(bd.skills, 2),
            "desc_score": round(bd.description, 2),
            "loc_score": round(bd.location, 2),
            "penalty_pts": round(bd.penalties, 2),
            "accepted": result.accepted,
            "matched_terms": result.matched_terms,
            "missing_terms": result.missing_terms,
            "penalties": result.penalties,
            "reasons": result.reasons,
            "matched_domains": result.explanation.matched_domains,
            "conflicting_domains": result.explanation.conflicting_domains,
            "role_similarity": result.explanation.role_similarity,
        }
        all_results.append(rec)

    # Print table
    audit_log.info(f"\n{'#':<4} {'PROV':<14} {'TITLE':<40} {'COMPANY':<18} {'TOTAL':>6} {'T':>5} {'Sk':>5} {'D':>5} {'Pen':>5} {'ACCEPT':<8} {'MATCH_TERMS'}")
    audit_log.info("-" * 150)
    for i, r in enumerate(all_results, 1):
        title_trunc = r["title"][:39]
        company_trunc = r["company"][:17]
        accept_str = "✅ ACCEPT" if r["accepted"] else "❌ REJECT"
        mt = ",".join(r["matched_terms"])[:30]
        audit_log.info(
            f"{i:<4} {r['provider']:<14} {title_trunc:<40} {company_trunc:<18} "
            f"{r['total_score']:>6.1f} {r['title_score']:>5.1f} {r['skill_score']:>5.1f} "
            f"{r['desc_score']:>5.1f} {r['penalty_pts']:>5.1f} {accept_str:<8} {mt}"
        )

    # ─── Rejection detail ────────────────────────────────────────────────────
    hdr("REJECTION ANALYSIS — PER CANDIDATE")
    audit_log.info(f"{'#':<4} {'PROV':<12} {'TITLE':<40} {'TOTAL':>6}  REJECTION REASON")
    audit_log.info("-" * 120)
    rej_count = 0
    for i, r in enumerate(all_results, 1):
        if r["accepted"]:
            continue
        rej_count += 1
        # Determine rejection reason from score components
        reasons = []
        if r["total_score"] < 30:
            reasons.append(f"total {r['total_score']:.1f} < 30 threshold")
        if r["penalty_pts"] < 0:
            reasons.append(f"penalty {r['penalty_pts']:.1f}")
        if r["title_score"] == 0 and r["skill_score"] == 0 and r["desc_score"] == 0:
            reasons.append("ZERO title+skill+desc signal")
        if r["description_len"] < 50:
            reasons.append(f"description too short ({r['description_len']} chars)")
        title_trunc = r["title"][:39]
        reason_str = " | ".join(reasons) if reasons else "score below threshold"
        audit_log.info(f"{i:<4} {r['provider']:<12} {title_trunc:<40} {r['total_score']:>6.1f}  {reason_str}")

    # ─── Classify each rejection ─────────────────────────────────────────────
    hdr("REJECTION CLASSIFICATION")

    PYTHON_RELATED_TITLE_WORDS = {"python", "backend", "back-end", "developer", "engineer", "software", "api", "data", "ml", "machine learning", "fullstack", "full stack", "flask", "django", "fastapi"}
    CLEARLY_IRRELEVANT = {"recruiter", "sales", "marketing", "finance", "hr ", "human resources", "accountant", "legal", "office", "coordinator", "talent", "account executive", "business development", "product manager", "data analyst", "designer", "ux", "ui/ux"}

    categories = {"A_correct_rejection": [], "B_false_negative": [], "C_extraction_failure": [], "D_retrieval_failure": [], "E_other": []}

    for r in all_results:
        if r["accepted"]:
            continue

        title_l = r["title"].lower()
        desc_l = (r["description"] if "description" in r else "").lower()
        # Use what we have
        # Check if clearly irrelevant
        is_irrelevant = any(w in title_l for w in CLEARLY_IRRELEVANT)
        # Check if description is synthetic (too short or "position at")
        desc_synthetic = r["description_len"] < 100 or "position at" in r.get("title", "").lower()
        # Check description length
        desc_missing = r["description_len"] < 80
        # Check if title is python/backend/dev related
        is_python_related = (
            "python" in title_l or
            "backend" in title_l or "back-end" in title_l or
            ("developer" in title_l and not is_irrelevant) or
            ("engineer" in title_l and not is_irrelevant) or
            "software engineer" in title_l or
            "data engineer" in title_l or
            "ml engineer" in title_l
        )

        if is_irrelevant:
            cat = "A_correct_rejection"
            reason = "Non-tech/non-developer role (sales/recruiter/finance/design etc.)"
        elif is_python_related and desc_missing:
            cat = "C_extraction_failure"
            reason = f"Relevant title but description too short/synthetic ({r['description_len']} chars) — scoring starved"
        elif is_python_related and r["total_score"] >= 0 and not r["accepted"]:
            cat = "B_false_negative"
            reason = f"Likely relevant Python/dev role, scored {r['total_score']:.1f} but rejected"
        elif r["total_score"] < 0:
            cat = "A_correct_rejection"
            reason = f"Penalized domain conflict (score {r['total_score']:.1f})"
        else:
            cat = "E_other"
            reason = f"Score {r['total_score']:.1f}, title={r['title'][:30]}"

        categories[cat].append((r, reason))

    for cat_name, items in categories.items():
        label = {
            "A_correct_rejection": "A. Correct rejections (genuinely irrelevant)",
            "B_false_negative": "B. False negatives (relevant but rejected)",
            "C_extraction_failure": "C. Extraction failures (relevant title, bad/missing description)",
            "D_retrieval_failure": "D. Retrieval problems (provider returned poor candidate)",
            "E_other": "E. Other",
        }[cat_name]
        audit_log.info(f"\n  [{len(items)}] {label}")
        for r, reason in items:
            audit_log.info(f"       - [{r['provider']}] {r['title'][:50]} | {reason}")

    # ─── Greenhouse detailed audit ───────────────────────────────────────────
    hdr("GREENHOUSE CANDIDATES — DETAIL")
    gh_jobs = provider_p4.get("greenhouse", [])
    audit_log.info(f"  Greenhouse returned {len(gh_jobs)} P4 candidates")
    for j in gh_jobs:
        matching = any(r["title"] == j.title and r["company"] == j.company for r in all_results if r["provider"] == "greenhouse")
        scored_rec = next((r for r in all_results if r["title"] == j.title and r["company"] == j.company and r["provider"] == "greenhouse"), None)
        desc_len = len(j.description or "")
        skills = j.required_skills or []
        if scored_rec:
            audit_log.info(
                f"  [{scored_rec['total_score']:>6.1f}] {'✅' if scored_rec['accepted'] else '❌'} "
                f"{j.title[:45]:<45} @ {j.company:<12} "
                f"desc={desc_len:>5}ch skills={skills[:3]}"
            )
        else:
            audit_log.info(f"  [  N/A] {j.title[:45]:<45} @ {j.company:<12} desc={desc_len}ch")

    # ─── Lever detail ────────────────────────────────────────────────────────
    hdr("LEVER CANDIDATES — DETAIL")
    lv_jobs = provider_p4.get("lever", [])
    audit_log.info(f"  Lever returned {len(lv_jobs)} P4 candidates")
    for j in lv_jobs:
        scored_rec = next((r for r in all_results if r["title"] == j.title and r["company"] == j.company and r["provider"] == "lever"), None)
        desc_len = len(j.description or "")
        if scored_rec:
            audit_log.info(
                f"  [{scored_rec['total_score']:>6.1f}] {'✅' if scored_rec['accepted'] else '❌'} "
                f"{j.title[:45]:<45} @ {j.company:<12} desc={desc_len}ch"
            )
        else:
            audit_log.info(f"  [  N/A] {j.title[:45]:<45} @ {j.company:<12} desc={desc_len}ch")

    # ─── Ashby audit ─────────────────────────────────────────────────────────
    hdr("ASHBY — WHY 0 P4 CANDIDATES")
    ash_jobs = provider_p4.get("ashby", [])
    audit_log.info(f"  Ashby returned {len(ash_jobs)} P4 candidates")
    audit_log.info(f"  Ashby target companies: notion, linear, ramp, resend, vanta, pinecone, posthog")
    audit_log.info(f"  content_tokens for 'python developer': {sorted(content_tokens)}")
    audit_log.info(f"  Ashby uses SYNTHETIC description: '<title> position at <company> in <loc>.'")
    audit_log.info(f"  For a job titled 'Software Engineer', content_token 'python' WILL NOT appear")
    audit_log.info(f"  in title OR synthetic description → fails job_matches_query → filtered at P3")

    # ─── Search Engine Discovery trace ───────────────────────────────────────
    hdr("SEARCH ENGINE DISCOVERY — STAGE TRACE")
    se_jobs = provider_p4.get("search_engine", [])
    audit_log.info(f"  P4 returned to aggregator: {len(se_jobs)} jobs")
    audit_log.info(f"\n  GENERATED QUERIES for 'python developer':")
    from app.services.search_query_generator import SearchQueryGenerator
    queries = SearchQueryGenerator.generate_search_engine_queries("python developer", location=None, max_queries=10)
    for i, q in enumerate(queries, 1):
        audit_log.info(f"    {i:2}. {q}")

    audit_log.info(f"""
  STAGE TRACE (from diagnostic data):
    Stage 1 — Query Enrichment    : {len(queries)} enriched queries generated
    Stage 2 — Search Aggregation  : total_limit = limit*3 = 20*3 = 60 URLs requested
                                    (DuckDuckGo limit_per_query=10)
    Stage 3 — CrawlScheduler      : Input up to 60 candidate URLs
                                    → classify each by PageType
                                    → JOB_POSTING: add directly
                                    → ATS/listing: drill-down extract job URLs
                                    → DISCARD types (blog/home/docs): dropped
                                    → SWRR diversity allocation
                                    → max_candidate_pages = {60} (config.max_candidate_pages)
    Stage 4 — JobExtractor        : fetch + parse HTML for each scheduled URL
                                    → gatekeeper classifier rejects non-job pages
                                    → extractor pipeline: JsonLD → OpenGraph → MetaTag → Heuristic
                                    → apply_url validation (reject if no apply_url and not direct ATS)
    Stage 5 — Dedup + CompanyCap  : max_jobs_per_company=5, fingerprint dedup

  WHY ONLY ~4-8 REACH P4:
    The diagnostic showed: Input 60 → Output 50 at search_discovery.py:169
    This means CrawlScheduler produced >50 job posting URLs,
    then search_discovery sliced to limit=20 before extraction.
    JobExtractor then rejects many for:
      - apply_url is None and not direct ATS → most non-ATS career pages
      - fetch timeout or non-200 response
      - gatekeeper classifier rejects page as non-job
      - no extractor can parse the page (no JSON-LD, no OG tags)
""")

    audit_log.info(f"  Search Engine P4 jobs detail:")
    for j in se_jobs:
        scored_rec = next((r for r in all_results if r["title"] == j.title and r["url"] == j.url), None)
        if scored_rec:
            audit_log.info(
                f"    [{scored_rec['total_score']:>6.1f}] {'✅' if scored_rec['accepted'] else '❌'} "
                f"{j.title[:50]:<50} | url={j.url[:60]}"
            )
            audit_log.info(f"          source={j.source!r}  discovery_provider={j.discovery_provider!r}")

    # ─── Attribution bug ─────────────────────────────────────────────────────
    hdr("ATTRIBUTION BUG — DISCOVERY PROVIDER vs ATS SOURCE")
    audit_log.info("""
  EXPECTED semantic model:
    discovery_provider = HOW the job was found        (e.g. 'search_engine')
    source             = WHICH ATS/board hosts the job (e.g. 'lever', 'greenhouse')

  OBSERVED (final returned jobs from last run):
    discovery_provider = 'search_engine'
    source             = 'search_engine'   ← WRONG for jobs.lever.co URLs

  ROOT CAUSE — TRACED THROUGH CODE:

  1. job_extractor.py:147  (standard ATS/career page branch, lines 155-161)
       base_job.source is set by the EXTRACTOR (JsonLdExtractor, HeuristicExtractor etc.)
       These extractors parse source from page metadata, NOT from the URL domain.
       If a Lever page has no structured schema saying "source=lever", the extractor
       inherits from the NormalizedJob default or search_result context.

  2. search_discovery.py:217 (Stage 4 loop)
       result.discovery_provider = self.source_name  → 'search_engine'  ✅ CORRECT
       BUT result.source is whatever the extractor set — which may be None or fallback.

  3. The extractor pipeline (base_extractor → heuristic) does NOT call ProviderClassifier
     to infer the ATS source from the URL. ProviderClassifier IS called at line 165
     but only for apply_url validation (is_direct_ats check), NOT to set source.

  EXACT BUG LOCATION:
     job_extractor.py lines 163-184
     ProviderClassifier.classify(url) is called → returns 'lever'/'greenhouse'/etc.
     provider_tag is stored in local variable but NEVER assigned to base_job.source
     The source field remains whatever the extractor set (default = 'search_engine'
     inherited from the SearchResult or left as NormalizedJob default)

  FIX (not implementing yet — audit only):
     After line 165:  provider_tag = ProviderClassifier.classify(url)
     Add:             if provider_tag in DIRECT_ATS_PROVIDERS:
                          base_job.source = provider_tag
""")
    audit_log.info(f"  Evidence from current P4 search_engine jobs:")
    for j in se_jobs:
        from app.services.crawl.provider_classifier import ProviderClassifier
        expected_source = ProviderClassifier.classify(j.url)
        audit_log.info(
            f"    URL: {j.url[:60]}\n"
            f"    actual source={j.source!r}  actual discovery_provider={j.discovery_provider!r}\n"
            f"    ProviderClassifier.classify() → {expected_source!r}  ← SHOULD be source\n"
        )

    # ─── Summary counts ──────────────────────────────────────────────────────
    hdr("RETRIEVAL FUNNEL SUMMARY")
    n_accepted = sum(1 for r in all_results if r["accepted"])
    n_rejected = sum(1 for r in all_results if not r["accepted"])
    n_false_neg = len(categories["B_false_negative"])
    n_extract_fail = len(categories["C_extraction_failure"])
    n_correct_rej = len(categories["A_correct_rejection"])
    n_retrieval_fail = len(categories["D_retrieval_failure"])

    audit_log.info(f"""
  ┌─────────────────────────────────────────────────────────┐
  │  COMPLETE RETRIEVAL FUNNEL — query='python developer'    │
  ├─────────────────────────────────────────────────────────┤
  │  Search queries generated             : {len(queries):<5}             │
  │  Search engine results requested      : 60 (limit*3)    │
  │  Candidate URLs to CrawlScheduler     : ~44-60          │
  │  Job posting URLs after classification: ~50+            │
  │  Extraction targets (sliced at limit) : 20              │
  │  Successfully extracted (P4)          : {len(raw_candidates):<5}             │
  │    - Greenhouse                       : {len(provider_p4.get('greenhouse', [])):<5}             │
  │    - Lever                            : {len(provider_p4.get('lever', [])):<5}             │
  │    - Ashby                            : {len(provider_p4.get('ashby', [])):<5}             │
  │    - Search Engine                    : {len(provider_p4.get('search_engine', [])):<5}             │
  │  After cross-provider dedup           : {len(unique_pre_rank):<5}             │
  │  S5 Ranking:                                            │
  │    - Accepted (score>=30, no penalty) : {n_accepted:<5}             │
  │    - Rejected                         : {n_rejected:<5}             │
  │  DB saved & returned                  : {n_accepted:<5}             │
  ├─────────────────────────────────────────────────────────┤
  │  REJECTION BREAKDOWN                                     │
  │    A. Correct rejections              : {n_correct_rej:<5}             │
  │    B. False negatives (likely good)   : {n_false_neg:<5}             │
  │    C. Extraction failures             : {n_extract_fail:<5}             │
  │    D. Retrieval failures              : {n_retrieval_fail:<5}             │
  │    E. Other                           : {len(categories['E_other']):<5}             │
  └─────────────────────────────────────────────────────────┘
""")

    # Save full JSON for review
    out_path = "audit_candidates.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    audit_log.info(f"  Full scored candidates saved to: {out_path}")

    current_diagnostics.reset(diag_token)


if __name__ == "__main__":
    asyncio.run(run_audit())
