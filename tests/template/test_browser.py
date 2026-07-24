"""BrowserManager 测试"""
import asyncio
from services.template.browser import BrowserManager


def test_browser_manager_singleton():
    """测试单例模式"""
    m1 = BrowserManager()
    m2 = BrowserManager()
    assert m1 is m2


def test_browser_manager_initial_state():
    """测试初始状态"""
    m = BrowserManager()
    assert m._browser is None
    assert m._playwright is None
