"""
Page Fetcher Service

Responsible ONLY for fetching raw HTML content from target career page URLs.
Implements fast static fetching via `httpx` and selective headless browser rendering via `Playwright` for JavaScript Single Page Apps (SPAs).
"""

import re
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class HttpFetcher:
    """
    Fast static HTTP page fetcher using httpx.
    """

    async def fetch(self, url: str, timeout: float = 10.0) -> Optional[str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Finder/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        import time
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                dur = time.time() - start
                if tracker:
                    tracker.record_fetch(url, status_code=response.status_code, duration=dur)
                if response.status_code == 200:
                    return response.text
                logger.warning(f"HttpFetcher got HTTP {response.status_code} for URL: {url}")
        except Exception as exc:
            dur = time.time() - start
            if tracker:
                tracker.record_fetch(url, status_code=None, duration=dur, error=str(exc))
            logger.warning(f"HttpFetcher failed for '{url}': {exc}")

        return None


class PlaywrightFetcher:
    """
    Headless Chromium browser rendering page fetcher using Playwright.
    Used selectively for JavaScript Single Page Applications (React, Vue, Angular).
    """

    async def fetch(self, url: str, timeout: float = 15.0) -> Optional[str]:
        import time
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()
        start = time.time()
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Finder/1.0"
                )
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
                await page.wait_for_timeout(1000)
                html = await page.content()
                await browser.close()
                dur = time.time() - start
                if tracker:
                    tracker.record_fetch(url, status_code=200, duration=dur, playwright_used=True)
                return html
        except Exception as exc:
            dur = time.time() - start
            if tracker:
                tracker.record_fetch(url, status_code=None, duration=dur, error=f"Playwright failed: {exc}", playwright_used=True)
            logger.warning(f"PlaywrightFetcher failed for '{url}': {exc}")

        return None


class SmartPageFetcher:
    """
    Orchestrates page fetching, selectively triggering Playwright when static HTML indicates a JS SPA shell.
    """

    def __init__(self, http_fetcher: Optional[HttpFetcher] = None, playwright_fetcher: Optional[PlaywrightFetcher] = None):
        self.http_fetcher = http_fetcher or HttpFetcher()
        self.playwright_fetcher = playwright_fetcher or PlaywrightFetcher()

    async def fetch(self, url: str) -> Optional[str]:
        # Tier 1: Try static HTTP fetch
        html = await self.http_fetcher.fetch(url)

        # Tier 2: Check if static HTML is a JavaScript SPA shell (only when we got real HTML)
        if html is not None and self._is_js_spa_shell(html):
            # Explicitly prevent Playwright on LinkedIn to avoid blocks and save resources
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            netloc = parsed_url.netloc.lower()
            if "linkedin.com" in netloc:
                logger.info(f"Skipping Playwright for LinkedIn URL to prevent blocks: '{url}'")
                return html

            logger.info(f"JS Single Page App detected for '{url}'. Triggering Playwright rendering...")
            rendered_html = await self.playwright_fetcher.fetch(url)
            if rendered_html and len(rendered_html) > len(html or ""):
                return rendered_html

        return html

    # Generic SPA root ids that many frameworks use. These are ambiguous on
    # their own — plenty of fully server-rendered pages also mount their app
    # at #root/#app while shipping complete content — so they only count as
    # a JS-shell signal when the page's visible text is also very short.
    _AMBIGUOUS_SPA_MOUNTS = [
        '<div id="root"></div>',
        '<div id="app"></div>',
        '<div id="mount"></div>',
        '<div id="__next"></div>',
        '<div class="loading"></div>',
    ]

    # Mount signatures distinctive enough to be a definitive JS-shell signal
    # by themselves, regardless of how much surrounding text the page has.
    #
    # Greenhouse's public job-board template (id="react-portal-mount-point")
    # renders an individual job posting URL
    # (boards.greenhouse.io/{company}/jobs/{id}) as the company's job INDEX
    # page in static HTML — real company description, "Current openings at
    # X" heading — with the specific job's content injected client-side into
    # this portal mount point. Because that index-page boilerplate is
    # substantial (often 2-3k+ characters), the ambiguous-mount text-length
    # check above never fires for these pages, so this id is checked
    # unconditionally. The id is specific to Greenhouse's embed architecture
    # and not a generic/common mount name, so it will not misfire on
    # unrelated fully-rendered pages.
    _DEFINITIVE_SPA_MOUNTS = [
        'id="react-portal-mount-point"',
    ]

    @staticmethod
    def _is_js_spa_shell(html: Optional[str]) -> bool:
        if not html:
            return True

        clean_html = html.strip().lower()

        # Definitive markers: presence alone means the real content is
        # client-side rendered, regardless of surrounding boilerplate length.
        for marker in SmartPageFetcher._DEFINITIVE_SPA_MOUNTS:
            if marker in clean_html:
                return True

        # Ambiguous markers: only treat as a shell if there's very little
        # surrounding text, since these ids are also used by fully
        # server-rendered pages.
        for mount in SmartPageFetcher._AMBIGUOUS_SPA_MOUNTS:
            if mount in clean_html:
                text_content = re.sub(r'<[^>]+>', '', clean_html).strip()
                if len(text_content) < 100:
                    return True

        # If html is extremely short and has almost zero text content
        text_content = re.sub(r'<[^>]+>', '', clean_html).strip()
        if len(clean_html) < 300 and len(text_content) < 20:
            return True

        return False
