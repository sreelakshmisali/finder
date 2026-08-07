"""
Deep-Dive Relevance Ranking Evidence Collection Script

Executes query 'React Developer' with full passive diagnostics enabled,
analyzing exact score calculations, negative penalties, provider metadata completeness,
SearchIntent parsing, RoleIntent extraction, technology tokenization, and provider bias.
"""

import asyncio
import json
import logging
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database.base import Base
from app.services.job_service import JobService
from app.schemas.job import JobSearchQuery
from app.services.search.query_intent_parser import QueryIntentParser
from app.services.search.role_intent_extractor import RoleIntentExtractor
from app.services.search.text_normalizer import TextNormalizer
from app.services.search.tech_taxonomy import TECH_TO_DOMAINS, DOMAIN_KEYWORDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        service = JobService(db)
        print("Executing search for query 'React Developer'...")
        search_query = JobSearchQuery(query="React Developer", limit=50)
        resp = await service.search_jobs(query=search_query)

    # Locate the generated diagnostic JSON file
    log_dir = os.path.join("logs", "search_diagnostics")
    if not os.path.exists(log_dir):
        log_dir = os.path.join("backend", "logs", "search_diagnostics")

    json_files = sorted([os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".json")], key=os.path.getmtime, reverse=True)
    latest_json = json_files[0]
    print(f"Latest JSON trace file: {latest_json}")

    with open(latest_json, "r", encoding="utf-8") as f:
        trace_data = json.load(f)

    print("\n" + "=" * 70)
    print("DEEP-DIVE RELEVANCE RANKING ANALYSIS SUMMARY")
    print("=" * 70)

    # 1. SearchIntent Parser
    search_context = QueryIntentParser.parse("React Developer")
    intent = search_context.intent
    print("\n--- 1. SEARCH INTENT PARSING ---")
    print(f"Raw Query: '{search_context.raw_query}'")
    print(f"Roles: {[t.name for t in intent.roles]}")
    print(f"Technologies: {[t.name for t in intent.technologies]}")
    print(f"Domains: {[t.name for t in intent.domains]}")

    # 2. Technology Tokenization Checks
    print("\n--- 2. TECHNOLOGY TOKENIZATION VERIFICATION ---")
    test_strings = [
        "react", "react.js", "reactjs", "react native", "react-native", "reactnative"
    ]
    for ts in test_strings:
        norm = TextNormalizer.normalize(ts)
        extracted = RoleIntentExtractor.extract(ts)
        print(f"Input: '{ts}' -> Normalized: '{norm}' -> Techs: {list(extracted.technologies)} -> Domains: {list(extracted.domains)}")

    # 3. Provider Bias & Score Distribution Analysis
    print("\n--- 3. PROVIDER SCORE & PENALTY DISTRIBUTION ---")
    ranking_records = trace_data.get("ranking", {}).get("records", [])
    provider_scores = {}
    for rec in ranking_records:
        prov = rec["provider"]
        if prov not in provider_scores:
            provider_scores[prov] = {
                "count": 0, "accepted": 0, "rejected": 0,
                "scores": [], "title_scores": [], "skills_scores": [],
                "desc_scores": [], "loc_scores": [], "penalties": []
            }
        ps = provider_scores[prov]
        ps["count"] += 1
        if rec["accepted"]: ps["accepted"] += 1
        else: ps["rejected"] += 1
        sc = rec["score"]
        sb = rec.get("score_breakdown", {})
        ps["scores"].append(sc)
        ps["title_scores"].append(sb.get("title_score", 0.0))
        ps["skills_scores"].append(sb.get("skills_score", 0.0))
        ps["desc_scores"].append(sb.get("description_score", 0.0))
        ps["loc_scores"].append(sb.get("location_score", 0.0))
        ps["penalties"].append(sb.get("penalties", 0.0))

    print(f"{'Provider':<18} | {'Total':<5} | {'Acc':<4} | {'Rej':<4} | {'Avg Score':<9} | {'Avg Title':<9} | {'Avg Skills':<10} | {'Avg Desc':<8} | {'Avg Pen':<8}")
    print("-" * 90)
    for prov, stats in provider_scores.items():
        c = max(stats["count"], 1)
        avg_s = sum(stats["scores"]) / c
        avg_t = sum(stats["title_scores"]) / c
        avg_sk = sum(stats["skills_scores"]) / c
        avg_d = sum(stats["desc_scores"]) / c
        avg_p = sum(stats["penalties"]) / c
        print(f"{prov:<18} | {stats['count']:<5} | {stats['accepted']:<4} | {stats['rejected']:<4} | {avg_s:<9.2f} | {avg_t:<9.2f} | {avg_sk:<10.2f} | {avg_d:<8.2f} | {avg_p:<8.2f}")

    # 4. Save Comprehensive Forensics Report
    out_file = os.path.join("scratch", "ranking_forensics_report.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, indent=2)
    print(f"\nSaved ranking forensics data to {out_file}")

if __name__ == "__main__":
    asyncio.run(main())
