"""
Container-safe Playwright browser launcher helper.

Provides a standardized way to launch Playwright browsers with proper
configuration for containerized environments and guaranteed cleanup.
"""

import logging
import os
from typing import Optional, List
from playwright.async_api import (
    async_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
)

logger = logging.getLogger(__name__)


def get_container_safe_browser_args() -> List[str]:
    """
    Get browser arguments optimized for containerized environments.
    
    These args prevent common issues in Docker containers:
    - --disable-dev-shm-usage: Use /tmp instead of /dev/shm (avoids small /dev/shm issues)
    - --no-sandbox: Required in containers
    - --disable-gpu: Not needed in headless containers
    - Additional stability flags
    
    Returns:
        List of browser arguments
    """
    return [
        "--no-sandbox",
        "--disable-dev-shm-usage",  # Critical for Docker containers
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-setuid-sandbox",
        "--disable-web-security",  # For some scraping scenarios
        "--disable-features=VizDisplayCompositor",
    ]


async def launch_browser_safe(
    playwright: Playwright,
    headless: bool = True,
    extra_args: Optional[List[str]] = None,
) -> Browser:
    """
    Launch a Chromium browser with container-safe configuration.
    
    Args:
        playwright: Playwright instance
        headless: Whether to run in headless mode
        extra_args: Additional browser arguments (merged with container-safe args)
        
    Returns:
        Browser instance
    """
    base_args = get_container_safe_browser_args()
    all_args = base_args + (extra_args or [])
    
    logger.debug(f"Launching browser with {len(all_args)} args (headless={headless})")
    
    browser = await playwright.chromium.launch(
        headless=headless,
        args=all_args,
    )
    
    logger.debug("Browser launched successfully")
    return browser


async def create_browser_context_safe(
    browser: Browser,
    viewport: Optional[dict] = None,
    **kwargs
) -> BrowserContext:
    """
    Create a browser context with safe defaults.
    
    Args:
        browser: Browser instance
        viewport: Optional viewport size (defaults to 1920x1080)
        **kwargs: Additional context options
        
    Returns:
        BrowserContext instance
    """
    default_viewport = {"width": 1920, "height": 1080}
    if viewport:
        default_viewport.update(viewport)
    
    context = await browser.new_context(
        viewport=default_viewport,
        **kwargs
    )
    
    logger.debug("Browser context created successfully")
    return context


async def create_page_safe(context: BrowserContext) -> Page:
    """
    Create a new page in the context.
    
    Args:
        context: BrowserContext instance
        
    Returns:
        Page instance
    """
    page = await context.new_page()
    logger.debug("Page created successfully")
    return page


async def cleanup_browser_safe(
    page: Optional[Page] = None,
    context: Optional[BrowserContext] = None,
    browser: Optional[Browser] = None,
    playwright: Optional[Playwright] = None,
    error_context: Optional[str] = None,
):
    """
    Safely clean up browser resources in correct order.
    
    Cleans up in order: page -> context -> browser -> playwright
    Logs errors but never raises exceptions (guaranteed cleanup).
    
    Args:
        page: Optional page to close
        context: Optional context to close
        browser: Optional browser to close
        playwright: Optional playwright instance to stop
        error_context: Optional context string for error logging
    """
    error_prefix = f"[{error_context}] " if error_context else ""
    
    try:
        if page:
            try:
                await page.close()
                logger.debug(f"{error_prefix}Page closed")
            except Exception as e:
                logger.warning(f"{error_prefix}Error closing page: {e}")
    except Exception as e:
        logger.warning(f"{error_prefix}Error in page cleanup: {e}")
    
    try:
        if context:
            try:
                await context.close()
                logger.debug(f"{error_prefix}Context closed")
            except Exception as e:
                logger.warning(f"{error_prefix}Error closing context: {e}")
    except Exception as e:
        logger.warning(f"{error_prefix}Error in context cleanup: {e}")
    
    try:
        if browser:
            try:
                await browser.close()
                logger.debug(f"{error_prefix}Browser closed")
            except Exception as e:
                logger.warning(f"{error_prefix}Error closing browser: {e}")
    except Exception as e:
        logger.warning(f"{error_prefix}Error in browser cleanup: {e}")
    
    try:
        if playwright:
            try:
                await playwright.stop()
                logger.debug(f"{error_prefix}Playwright stopped")
            except Exception as e:
                logger.warning(f"{error_prefix}Error stopping playwright: {e}")
    except Exception as e:
        logger.warning(f"{error_prefix}Error in playwright cleanup: {e}")





