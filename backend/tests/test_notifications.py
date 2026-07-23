"""
Unit tests for Job Notification Pipeline & Schemas.
"""

import asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.notification import NotificationResponse, NotificationUnreadCountResponse, PipelineRunResponse


def test_notification_schemas():
    notif_id = uuid.uuid4()
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    res = NotificationResponse(
        id=notif_id,
        user_id=user_id,
        job_id=job_id,
        type="high_match_job",
        title="⚡ High Match (88%): Python Backend Developer",
        message="Stripe in San Francisco, CA. Strong FastAPI & PostgreSQL alignment.",
        read=False,
        created_at="2026-07-23T15:00:00Z"
    )
    assert res.read is False
    assert "High Match" in res.title

    count_res = NotificationUnreadCountResponse(unread_count=3)
    assert count_res.unread_count == 3

    pipeline_res = PipelineRunResponse(
        user_id=user_id,
        saved_searches_processed=2,
        jobs_evaluated=25,
        new_notifications_created=3,
        message="Pipeline completed: 3 new alerts"
    )
    assert pipeline_res.new_notifications_created == 3

    print("test_notification_schemas: PASSED")


if __name__ == "__main__":
    test_notification_schemas()
