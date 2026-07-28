import asyncio
import sys
import os

# Insert current directory into path
sys.path.insert(0, '.')

from app.providers.search_engine.search_discovery import SearchDiscoveryProvider
from app.providers.base_discovery import DiscoveryContext
from app.schemas.job import JobSearchQuery

async def main():
    discovery = SearchDiscoveryProvider()
    query = JobSearchQuery(
        query="react",
        location="Remote",
        force_refresh=True,
        limit=50
    )
    context = DiscoveryContext(query=query)
    print("Starting search via SearchDiscoveryProvider...")
    
    # Initialize tracker in context metadata
    tracker = context.metadata.get("tracker")
    if tracker:
        tracker.start_stage("Stage 1 - Search Engine Discovery")
        
    jobs = await discovery.discover(context)
    print(f"Scraped {len(jobs)} jobs.")

    if tracker:
        tracker.complete()
        from app.utils.pipeline_report_generator import PipelineReportGenerator
        
        # Save under logs directory in backend
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(base_dir, "logs")
        PipelineReportGenerator.write_reports(tracker, logs_dir)
        
        # Also save to conversation artifacts directory for visibility
        artifacts_dir = r"C:\Users\codel\.gemini\antigravity\brain\00c5547d-eb3b-4b6e-9e36-b8c5556065e7"
        if os.path.exists(artifacts_dir):
            try:
                PipelineReportGenerator.write_reports(tracker, artifacts_dir)
            except Exception as e:
                print(f"Failed to copy report to artifact dir: {e}")
                
        # Print the text report to stdout so it's visible in the logs!
        report_path = os.path.join(logs_dir, "pipeline_report.txt")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                print("\n" + "=" * 80)
                print("                     PIPELINE REPORT OUTPUT")
                print("=" * 80)
                print(f.read())

if __name__ == "__main__":
    asyncio.run(main())
