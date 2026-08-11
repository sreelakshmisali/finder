"""
Pipeline Tracker — DISABLED

This module previously defined PipelineTracker, a per-request observability class
that recorded every stage of the discovery pipeline (crawl scheduling, extraction,
deduplication, persistence) into structured events.

It has been superseded by SearchDiagnosticsTracker (search_diagnostics.py), which
is the active observability system.  SearchDiagnosticsTracker uses the same
contextvars pattern and its context variable IS set by job_service.py, so all
`if diag:` guards in job_repository.py and elsewhere evaluate to True and
produce real output.

PipelineTracker's context variable (`current_tracker`) was never set anywhere in
the production call path, so every `tracker = current_tracker.get()` call returned
None and every `if tracker:` guard short-circuited silently.

The class is removed here to avoid maintaining dead code.  The context var is kept
as a module-level symbol so the `from app.utils.pipeline_tracker import current_tracker`
import in job_repository.py continues to resolve without changes; `current_tracker`
will always return None, and the existing `if tracker:` guards already handle that
gracefully.
"""

import contextvars

# Context variable kept for import compatibility.
# It is never set by any caller, so .get() always returns None.
current_tracker: contextvars.ContextVar = contextvars.ContextVar(
    "current_tracker", default=None
)
