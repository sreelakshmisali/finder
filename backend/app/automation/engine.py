"""
Playwright Engine Launcher

Utility for launching Playwright async browser instances in headless or visual mode.
"""

import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)


class PlaywrightEngine:
    """
    Context manager / helper for launching Playwright browsers.
    """

    @staticmethod
    async def get_browser(headless: bool = True) -> Browser:
        """
        Launches Chromium browser instance.
        """
        p = await async_playwright().start()
        browser = await p.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        return browser

    @staticmethod
    async def create_page(browser: Browser) -> Page:
        """
        Creates a new browser context with modern viewport and user-agent.
        """
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        return page
