"""Playwright 浏览器单例管理"""
from typing import Optional

from playwright.async_api import Browser, Playwright, async_playwright

from .exceptions import BrowserNotAvailableError


class BrowserManager:
    """Playwright 浏览器单例（同步使用，不并发）"""

    _instance: Optional["BrowserManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def get_browser(self) -> Browser:
        """获取浏览器实例（懒初始化）"""
        if self._browser is None or not self._browser.is_connected():
            await self._start_browser()
        return self._browser

    async def _start_browser(self):
        """启动 Playwright"""
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        except Exception as e:
            raise BrowserNotAvailableError(f"Failed to start browser: {e}")

    async def close(self):
        """关闭浏览器"""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
