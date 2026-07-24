import unittest
from datetime import datetime
from uuid import uuid4

from app.schemas.job import NormalizedJob
from app.models.job import Job
from app.services.dedup import DuplicateDetectionService

def create_db_job(company: str, title: str, location: str, description: str, url: str) -> Job:
    return Job(
        id=uuid4(),
        company=company,
        title=title,
        location=location,
        description=description,
        url=url,
        source="ats",
        remote=True,
        posted_date=datetime.utcnow()
    )

def create_norm_job(company: str, title: str, location: str, description: str, url: str) -> NormalizedJob:
    return NormalizedJob(
        company=company,
        title=title,
        location=location,
        description=description,
        url=url,
        source="google",
        remote=True
    )

class TestDuplicateDetection(unittest.TestCase):
    def setUp(self):
        self.dedup_service = DuplicateDetectionService()

    def test_identical_jobs(self):
        db_job = create_db_job("Stripe", "Backend Engineer", "Remote", "Great job", "http://x")
        norm_job = create_norm_job("Stripe", "Backend Engineer", "Remote", "Great job", "http://y")
        
        result = self.dedup_service.compare(norm_job, db_job)
        self.assertTrue(result.is_duplicate)
        self.assertGreater(result.score, 0.95)

    def test_company_aliases(self):
        db_job = create_db_job("Stripe, Inc.", "Backend Engineer", "Remote", "Great job", "http://x")
        norm_job = create_norm_job("Stripe", "Backend Engineer", "Remote", "Great job", "http://y")
        
        result = self.dedup_service.compare(norm_job, db_job)
        self.assertTrue(result.is_duplicate)
        self.assertGreaterEqual(result.matched_fields["company"], 0.75)

    def test_title_variations(self):
        db_job = create_db_job("Google", "Senior Backend Engineer Python", "Remote", "Great job", "http://x")
        norm_job = create_norm_job("Google", "Backend Engineer", "Remote", "Great job", "http://y")
        
        result = self.dedup_service.compare(norm_job, db_job)
        self.assertGreater(result.score, 0.7)

    def test_missing_description(self):
        db_job = create_db_job("Netflix", "Data Scientist", "Los Angeles", "Full desc ...", "http://x")
        norm_job = create_norm_job("Netflix", "Data Scientist", "Los Angeles", "", "http://y")
        
        result = self.dedup_service.compare(norm_job, db_job)
        # Should still be a duplicate because company, title, location are exact matches
        self.assertTrue(result.is_duplicate)

    def test_unrelated_jobs(self):
        db_job = create_db_job("Stripe", "Backend Engineer", "Remote", "Great job", "http://x")
        norm_job = create_norm_job("Airbnb", "Frontend Developer", "San Francisco", "UI job", "http://y")
        
        result = self.dedup_service.compare(norm_job, db_job)
        self.assertFalse(result.is_duplicate)
        self.assertLess(result.score, 0.5)

if __name__ == '__main__':
    unittest.main()
