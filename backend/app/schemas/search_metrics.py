"""
Search Metrics Schema

Data structures for observing and logging the performance of the job discovery pipeline.
"""

from typing import Optional
from pydantic import BaseModel, Field

class SearchMetrics(BaseModel):
    # Discovery
    search_queries_generated: int = Field(0, description="Number of expanded search queries")
    search_results_received: int = Field(0, description="Total candidate URLs returned by search engines")
    candidate_urls_scored: int = Field(0, description="Number of candidate URLs scored")
    candidate_urls_rejected: int = Field(0, description="Number of candidate URLs dropped before crawl")
    
    # Crawling
    crawl_attempts: int = Field(0, description="Number of HTTP fetches attempted")
    crawl_failures: int = Field(0, description="Number of failed HTTP fetches")
    playwright_fallback_count: int = Field(0, description="Number of times Playwright was invoked")
    
    # Extraction
    pages_processed: int = Field(0, description="Number of individual job pages sent to JobExtractor")
    jobs_found: int = Field(0, description="Number of jobs successfully parsed")
    jobs_invalid: int = Field(0, description="Number of jobs that failed parsing")
    
    # Ranking
    average_score: float = Field(0.0, description="Average relevance score of accepted jobs")
    filtered_percentage: float = Field(0.0, description="Percentage of extracted jobs filtered out by ranker")
    
    def calculate_aggregates(self, total_extracted: int, total_filtered: int, total_score: int):
        """Helper to calculate percentage and average score."""
        if total_extracted > 0:
            self.filtered_percentage = round((total_filtered / total_extracted) * 100, 2)
            accepted = total_extracted - total_filtered
            if accepted > 0:
                self.average_score = round(total_score / accepted, 2)
