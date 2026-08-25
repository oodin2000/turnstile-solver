# src/core/solver.py
import asyncio
import traceback
from typing import Optional

from .pool import BrowserPool, TurnstileResult
from .logger import setup_logger

logger = setup_logger("Solver")

_pool: Optional[BrowserPool] = None


class TurnstileSolver:
    def __init__(self, headless: bool = True, pool_size: int = 1):
        self.headless = headless
        self.pool_size = pool_size

    @classmethod
    async def start_pool(cls, headless: bool = True, pool_size: int = 1):
        global _pool
        if _pool is not None:
            logger.warning("Pool already started, skipping.")
            return
        _pool = BrowserPool(pool_size=pool_size, headless=headless)
        await _pool.start()
        logger.info(f"Pool started with {pool_size} workers (headless={headless})")

    @classmethod
    async def close_pool(cls):
        global _pool
        if _pool is None:
            return
        await _pool.close()
        _pool = None
        logger.info("Pool closed.")

    @classmethod
    async def solve(
        cls,
        url: str,
        sitekey: str,
        action: Optional[str] = None,
        cdata: Optional[str] = None,
        page_data: Optional[str] = None,
        timeout: int = 45,
    ) -> TurnstileResult:
        if _pool is None:
            raise RuntimeError("Pool not started. Call start_pool() first.")
        
        logger.info(f"Solving for {url} with sitekey {sitekey[:8]}...")
        try:
            result = await _pool.solve(
                url=url,
                sitekey=sitekey,
                action=action,
                cdata=cdata,
                page_data=page_data,
                timeout=timeout,
            )
            return result
        except Exception as e:
            logger.error(f"Error during solve: {e}\n{traceback.format_exc()}")
            return TurnstileResult(
                token=None,
                elapsed=0.0,
                status="failed",
                error=str(e),
            )

    @property
    def queue_size(self) -> int:
        if _pool is None:
            return 0
        return _pool.queue_size
