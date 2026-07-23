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
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.text
                logger.warning(f"HttpFetcher got HTTP {response.status_code} for URL: {url}")
        except Exception as exc:
            logger.warning(f"HttpFetcher failed for '{url}': {exc}")

        return None


class PlaywrightFetcher:
    """
    Headless Chromium browser rendering page fetcher using Playwright.
    Used selectively for JavaScript Single Page Applications (React, Vue, Angular).
    """

    async def fetch(self, url: str, timeout: float = 15.0) -> Optional[str]:
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
                return html
        except Exception as exc:
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

        # Tier 2: Check if static HTML is a JavaScript SPA shell
        if self._is_js_spa_shell(html):
            logger.info(f"JS Single Page App detected for '{url}'. Triggering Playwright rendering...")
            rendered_html = await self.playwright_fetcher.fetch(url)
            if rendered_html and len(rendered_html) > len(html or ""):
                return rendered_html

        return html

    @staticmethod
    def _is_js_spa_shell(html: Optional[str]) -> bool:
        if not html:
            return True

        clean_html = html.strip().lower()

        # Check for explicit SPA container mounts with minimal inner text
        spa_mounts = [
            '<div id="root"></div>',
            '<div id="app"></div>',
            '<div id="mount"></div>',
            '<div id="__next"></div>',
            '<div class="loading"></div>'
        ]

        for mount in spa_mounts:
            if mount in clean_html:
                text_content = re.sub(r'<[^>]+>', '', clean_html).strip()
                if len(text_content) < 100:
                    return True

        # If html is extremely short and has almost zero text content
        text_content = re.sub(r'<[^>]+>', '', clean_html).strip()
        if len(clean_html) < 300 and len(text_content) < 20:
            return True

        return False
