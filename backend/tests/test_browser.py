"""Tests for browser manager."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.browser import BrowserManager


@pytest.fixture
def browser_manager():
    """Create browser manager instance."""
    return BrowserManager()


@pytest.mark.asyncio
async def test_browser_start_stop(browser_manager):
    """Test browser lifecycle management."""
    # Start browser
    await browser_manager.start()
    assert browser_manager._browser is not None
    assert browser_manager._playwright is not None

    # Stop browser
    await browser_manager.stop()
    assert browser_manager._browser is None
    assert browser_manager._playwright is None


@pytest.mark.asyncio
async def test_browser_context_manager():
    """Test context manager for browser context."""
    manager = BrowserManager()

    with patch("app.services.browser.async_playwright") as mock_playwright:
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.close = AsyncMock()

        async with manager.new_context(viewport={"width": 1280, "height": 720}) as ctx:
            assert ctx == mock_context
            mock_browser.new_context.assert_called_once()

        mock_context.close.assert_called_once()


@pytest.mark.asyncio
async def test_browser_new_page():
    """Test creating a new page."""
    manager = BrowserManager()

    with patch("app.services.browser.async_playwright") as mock_playwright:
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.close = AsyncMock()
        mock_context.close = AsyncMock()

        async with manager.new_page() as page:
            assert page == mock_page

        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()


@pytest.mark.asyncio
async def test_scrape_page():
    """Test page scraping functionality."""
    manager = BrowserManager()

    with patch("app.services.browser.async_playwright") as mock_playwright:
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html>Test Content</html>")
        mock_page.evaluate = AsyncMock(return_value="Test Text")
        mock_page.title = AsyncMock(return_value="Test Title")
        mock_page.close = AsyncMock()
        mock_context.close = AsyncMock()

        result = await manager.scrape_page(
            url="https://example.com", wait_for_selector="body"
        )

        assert result["html"] == "<html>Test Content</html>"
        assert result["text"] == "Test Text"
        assert result["title"] == "Test Title"

        mock_page.goto.assert_called_once()
        mock_page.wait_for_selector.assert_called_once_with("body", timeout=30000)


@pytest.mark.asyncio
async def test_scrape_page_without_selector():
    """Test page scraping without wait selector."""
    manager = BrowserManager()

    with patch("app.services.browser.async_playwright") as mock_playwright:
        mock_pw = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html>Test</html>")
        mock_page.evaluate = AsyncMock(return_value="Test")
        mock_page.title = AsyncMock(return_value="Test")
        mock_page.close = AsyncMock()
        mock_context.close = AsyncMock()

        result = await manager.scrape_page(url="https://example.com")

        assert "html" in result
        mock_page.goto.assert_called_once()
        # Should not call wait_for_selector
        mock_page.wait_for_selector.assert_not_called()
