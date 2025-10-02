"""Browser automation service using Playwright for web scraping."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from playwright.async_api import Browser, BrowserContext, Page, async_playwright


class BrowserManager:
    """Manages Playwright browser instances with context isolation."""

    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        """Initialize Playwright and launch browser."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )

    async def stop(self) -> None:
        """Close browser and cleanup Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    @asynccontextmanager
    async def new_context(self, **kwargs) -> AsyncGenerator[BrowserContext, None]:
        """
        Create a new browser context with custom settings.

        Args:
            **kwargs: Additional context options (viewport, user_agent, etc.)

        Yields:
            BrowserContext: Isolated browser context
        """
        await self.start()

        # Default context settings for EU financial sites
        default_settings = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "locale": "en-GB",
            "timezone_id": "Europe/London",
        }

        settings = {**default_settings, **kwargs}
        context = await self._browser.new_context(**settings)

        try:
            yield context
        finally:
            await context.close()

    @asynccontextmanager
    async def new_page(self, **context_kwargs) -> AsyncGenerator[Page, None]:
        """
        Create a new page in an isolated context.

        Args:
            **context_kwargs: Additional context options

        Yields:
            Page: New browser page
        """
        async with self.new_context(**context_kwargs) as context:
            page = await context.new_page()
            try:
                yield page
            finally:
                await page.close()

    async def scrape_page(
        self,
        url: str,
        wait_for_selector: str | None = None,
        timeout: int = 30000,
        **context_kwargs,
    ) -> dict[str, str | None]:
        """
        Scrape a page and return content.

        Args:
            url: URL to scrape
            wait_for_selector: CSS selector to wait for before extracting content
            timeout: Page load timeout in milliseconds
            **context_kwargs: Additional context options

        Returns:
            dict with 'html', 'text', and 'title' keys
        """
        async with self.new_page(**context_kwargs) as page:
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")

            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=timeout)

            html = await page.content()
            text = await page.evaluate("() => document.body.innerText")
            title = await page.title()

            return {
                "html": html,
                "text": text,
                "title": title,
            }


# Global browser manager instance
browser_manager = BrowserManager()
