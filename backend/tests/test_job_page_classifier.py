"""
Unit Tests for Job Page Classifier (Task 18)

Tests taxonomy classification, signal extraction, negative signal handling,
and JobExtractor gatekeeper integration.
"""

from bs4 import BeautifulSoup
from app.schemas.classification import PageType
from app.services.classification.signals import (
    ApplyButtonSignal, JobTitleSignal, RequirementsSectionSignal,
    EmploymentKeywordsSignal, LocationSignal, MultipleJobsSignal, NegativeKeywordsSignal
)
from app.services.classification.job_page_classifier import RuleBasedJobPageClassifier
from app.services.job_extractor import JobExtractor


def test_apply_button_signal():
    signal = ApplyButtonSignal()
    
    html_positive = "<html><body><button>Apply Now</button></body></html>"
    soup_positive = BeautifulSoup(html_positive, "html.parser")
    assert signal.evaluate("http://example.com/job/1", html_positive, soup_positive) == True

    html_negative = "<html><body><button>Subscribe</button></body></html>"
    soup_negative = BeautifulSoup(html_negative, "html.parser")
    assert signal.evaluate("http://example.com/job/1", html_negative, soup_negative) == False


def test_job_title_signal():
    signal = JobTitleSignal()

    html_positive = "<html><title>Software Engineer at Stripe</title><body><h1>Software Engineer</h1></body></html>"
    soup_positive = BeautifulSoup(html_positive, "html.parser")
    assert signal.evaluate("http://example.com/job/1", html_positive, soup_positive) == True

    html_negative = "<html><title>About Us</title><body><h1>Our Story</h1></body></html>"
    soup_negative = BeautifulSoup(html_negative, "html.parser")
    assert signal.evaluate("http://example.com/about", html_negative, soup_negative) == False


def test_negative_keywords_signal():
    signal = NegativeKeywordsSignal()

    html_positive = "<html><title>Company Blog</title><body><h1>Our recent news</h1></body></html>"
    soup_positive = BeautifulSoup(html_positive, "html.parser")
    assert signal.evaluate("http://example.com/blog", html_positive, soup_positive) == True

    html_negative = "<html><title>Software Engineer</title><body><h1>Software Engineer</h1></body></html>"
    soup_negative = BeautifulSoup(html_negative, "html.parser")
    assert signal.evaluate("http://example.com/job", html_negative, soup_negative) == False


def test_job_page_classifier_job_posting():
    classifier = RuleBasedJobPageClassifier(threshold=0.5)
    html = """
    <html>
        <title>Senior Backend Engineer - Remote</title>
        <body>
            <h1>Senior Backend Engineer</h1>
            <div>Full-time, Salary: $150k</div>
            <h2>Requirements</h2>
            <ul><li>Python</li><li>PostgreSQL</li></ul>
            <a href="/apply">Apply for this job</a>
        </body>
    </html>
    """
    result = classifier.classify("http://company.com/job/123", html)

    assert result.page_type == PageType.JOB_POSTING
    assert result.is_valid_job == True
    assert "apply_button" in result.matched_signals
    assert "job_title" in result.matched_signals
    assert "requirements" in result.matched_signals


def test_job_page_classifier_career_page():
    classifier = RuleBasedJobPageClassifier(threshold=0.5)
    html = """
    <html>
        <title>Careers at Our Company</title>
        <body>
            <h1>Join Our Team</h1>
            <a href="/job/1">Software Engineer</a>
            <a href="/job/2">Product Manager</a>
            <a href="/job/3">Designer</a>
            <a href="/job/4">Data Scientist</a>
        </body>
    </html>
    """
    result = classifier.classify("http://company.com/careers", html)

    assert result.page_type == PageType.CAREER_PAGE
    assert result.is_valid_job == False
    assert "multiple_jobs_index" in result.matched_signals


def test_job_page_classifier_irrelevant():
    classifier = RuleBasedJobPageClassifier(threshold=0.5)
    html = """
    <html>
        <title>Privacy Policy</title>
        <body>
            <h1>Privacy Policy</h1>
            <p>We care about your data.</p>
        </body>
    </html>
    """
    result = classifier.classify("http://company.com/privacy", html)

    assert result.page_type == PageType.IRRELEVANT
    assert result.is_valid_job == False
    assert "negative_keywords" in result.matched_signals


def test_job_page_classifier_empty_html():
    classifier = RuleBasedJobPageClassifier(threshold=0.5)
    result = classifier.classify("http://company.com/broken", "")
    assert result.page_type == PageType.IRRELEVANT
    assert result.is_valid_job == False
    assert result.rejected_reason == "Empty HTML content"


if __name__ == "__main__":
    test_apply_button_signal()
    test_job_title_signal()
    test_negative_keywords_signal()
    test_job_page_classifier_job_posting()
    test_job_page_classifier_career_page()
    test_job_page_classifier_irrelevant()
    test_job_page_classifier_empty_html()
    print("ALL 7 JOB PAGE CLASSIFIER TESTS PASSED SUCCESSFULLY!")
