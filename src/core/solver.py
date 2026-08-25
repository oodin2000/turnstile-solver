"""
solver.py — Thin async wrapper around BrowserPool.

Keeps the TurnstileSolver class name so existing imports don't break,
but delegates all browser management to BrowserPool.
"""

from typing import Optional

from .pool import BrowserPool, TurnstileResult

_pool: Optional[BrowserPool] = None


class TurnstileSolver:
    """
    Async Turnstile solver backed by a shared BrowserPool.

    Instantiate as many of these as you like — they all share the
    same underlying pool of browsers.
    """

    def __init__(self, headless: bool = True, pool_size: int = 3):
        global _pool
        if _pool is None:
            _pool = BrowserPool(pool_size=pool_size, headless=headless)

    @staticmethod
    async def start_pool(headless: bool = True, pool_size: int = 3):
        """Call once at application startup to launch all browsers."""
        global _pool
        if _pool is None:
            _pool = BrowserPool(pool_size=pool_size, headless=headless)
        await _pool.start()

    @staticmethod
    async def close_pool():
        """Call once at application shutdown to close all browsers."""
        global _pool
        if _pool is not None:
            await _pool.close()
            _pool = None

    async def solve(
        self,
        url: str,
        sitekey: str,
        action: Optional[str] = None,
        cdata: Optional[str] = None,
        page_data: Optional[str] = None,
        timeout: int = 45,
    ) -> TurnstileResult:
        if _pool is None:
            raise RuntimeError(
                "Pool not started. Call await TurnstileSolver.start_pool() first."
            )
        return await _pool.solve(
            url=url,
            sitekey=sitekey,
            action=action,
            cdata=cdata,
            page_data=page_data,
            timeout=timeout,
        )

    @property
    def queue_size(self) -> int:
        return _pool.queue_size if _pool else 0
