"""
Unit tests for Saved Searches feature.
"""

import asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.saved_search import SavedSearchCreate, SavedSearchResponse


def test_saved_search_schemas():
    payload = SavedSearchCreate(
        name="Python Remote Jobs",
        query="Python Backend",
        filters={"location": "India", "remote_only": True}
    )
    assert payload.name == "Python Remote Jobs"
    assert payload.query == "Python Backend"
    assert payload.filters["remote_only"] is True

    print("test_saved_search_schemas: PASSED")


if __name__ == "__main__":
    test_saved_search_schemas()
