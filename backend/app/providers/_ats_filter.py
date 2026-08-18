"""
ATS Provider Query-Relevance Filter
====================================
Lightweight, deterministic token filter applied inside each ATS provider's
per-company discovery loop, *before* the per-company fairness cap.

Goal
----
Remove jobs that share zero content with the user's query while keeping the
filter permissive enough that the downstream RelevanceRankingService still
handles precision.  Obvious mismatches (HR / Sales / Finance roles when the
user searches "React Developer") are eliminated; borderline matches (a generic
"Backend Engineer" posting for a "Python Developer" query) survive and let the
ranker decide.

Strategy
--------
1. Extract "content tokens" from the query — any word that is NOT a generic
   role/function/seniority term (developer, engineer, senior, …).
2. If no content tokens survive (pure generic query such as "Software Engineer"),
   skip filtering entirely so recall is fully preserved.
3. Otherwise accept a job when ANY content token appears as a case-insensitive
   substring in the job *title* (checked first, short-circuits) or *description*.
4. Tokens containing a dot (node.js, react.js, asp.net) also contribute their
   left-hand base form so that "react.js" still matches "Senior React Developer".

This runs without any LLM call, no hardcoded role/skill/technology lists beyond
the generic-word stoplist, and does not modify the global RelevanceRankingService.

Public API
----------
    extract_content_tokens(query: str) -> frozenset[str]
    job_matches_query(title: str, description: str, content_tokens: frozenset) -> bool
"""

import re
from typing import FrozenSet

# ---------------------------------------------------------------------------
# Generic words that carry no discriminating signal in a job search query.
# When *every* query token is in this set the filter becomes a no-op so that
# generic searches ("Software Engineer", "Full Stack Developer") still return
# the full, unfiltered candidate set.
# ---------------------------------------------------------------------------
_GENERIC_WORDS: FrozenSet[str] = frozenset({
    # Role / function
    "developer", "engineer", "manager", "director", "lead", "head",
    "architect", "designer", "analyst", "consultant", "specialist",
    "scientist", "coordinator", "programmer", "coder", "advisor",
    "associate", "partner", "executive", "officer", "recruiter",
    # Seniority / level
    "senior", "junior", "mid", "staff", "principal", "intern",
    "entry", "experienced", "expert", "contractor",
    # Generic tech descriptors
    "software", "technical", "technology", "tech", "it",
    "full", "stack", "fullstack", "remote", "hybrid", "onsite",
    "new", "grad", "graduate",
    # English stop words that occasionally appear in raw queries
    "and", "or", "for", "at", "in", "of", "the", "a",
})


def extract_content_tokens(query: str) -> FrozenSet[str]:
    """
    Return the set of "content tokens" from *query*: words that survive after
    stripping generic role/seniority/stop-words.

    Examples
    --------
    >>> extract_content_tokens("React Developer")
    frozenset({'react'})

    >>> extract_content_tokens("Python Backend Engineer")
    frozenset({'python', 'backend'})

    >>> extract_content_tokens("Django Developer")
    frozenset({'django'})

    >>> extract_content_tokens("DevOps Engineer")
    frozenset({'devops'})

    >>> extract_content_tokens("Software Engineer")   # all generic
    frozenset()

    >>> extract_content_tokens("")                    # empty → no filter
    frozenset()
    """
    if not query:
        return frozenset()

    # Tokenise: letters, digits, and common tech punctuation (#, ., +)
    tokens = re.findall(r"[a-z0-9#.+]+", query.lower())

    significant: set = {t for t in tokens if t not in _GENERIC_WORDS and len(t) > 1}

    # For dotted tokens (e.g. "react.js", "node.js", "asp.net") also add the
    # base form so "react.js Developer" still matches "Senior React Developer".
    extras: set = set()
    for t in significant:
        if "." in t:
            base = t.split(".")[0]
            if len(base) > 1 and base not in _GENERIC_WORDS:
                extras.add(base)

    return frozenset(significant | extras)


def job_matches_query(
    title: str,
    description: str,
    content_tokens: FrozenSet[str],
) -> bool:
    """
    Return True when *job* is relevant to the query represented by
    *content_tokens*.

    Rules
    -----
    - Empty *content_tokens* (pure generic / empty query) → always True.
    - Otherwise True when ANY token is a substring of *title* (checked first,
      short-circuits) or, if the title check fails, of *description*.

    Substring matching is intentionally permissive: "react" matches both
    "React Developer" and "Senior React/Redux Engineer".  The global
    RelevanceRankingService handles finer distinctions.
    """
    if not content_tokens:
        return True  # no meaningful filter → preserve full recall

    title_lower = title.lower()
    if any(tok in title_lower for tok in content_tokens):
        return True

    desc_lower = description.lower()
    return any(tok in desc_lower for tok in content_tokens)
