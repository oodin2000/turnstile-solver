"""
pool.py — Browser pool with async queue.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from camoufox.async_api import AsyncCamoufox

from .logger import setup_logger

logger = setup_logger("Pool")

ALLOWED_HOSTS = (
    "challenges.cloudflare.com",
    "cf-assets.cloudflare.com",
)

FIREFOX_PREFS = {
    "browser.startup.page": 0,
    "browser.startup.homepage": "about:blank",
    "network.dns.disablePrefetch": True,
    "network.prefetch-next": False,
    "network.predictor.enabled": False,
    "network.http.speculative-parallel-limit": 0,
    "network.http.max-persistent-connections-per-server": 12,
    "toolkit.shutdown.fastShutdownStage": 3,
    "media.gmp-manager.updateEnabled": False,
    "media.gmp-manager.url": "",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Turnstile</title>
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async></script>
</head>
<body><!-- cf turnstile --></body>
</html>"""


@dataclass
class SolveJob:
    url: str
    sitekey: str
    action: Optional[str]
    cdata: Optional[str]
    page_data: Optional[str]
    timeout: int
    future: asyncio.Future = field(default_factory=asyncio.Future)


@dataclass
class TurnstileResult:
    token: Optional[str]
    elapsed: float
    status: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "elapsed": self.elapsed,
            "status": self.status,
            "error": self.error,
        }


class BrowserWorker:
    def __init__(self, worker_id: int, queue: asyncio.Queue, headless: bool):
        self.worker_id = worker_id
        self.queue = queue
        self.headless = headless
        self._browser = None
        self._task: Optional[asyncio.Task] = None
        self._is_closing = False
        self._browser_lock = asyncio.Lock()

    async def start(self):
        logger.info(f"[W{self.worker_id}] Launching browser...")
        await self._ensure_browser()
        logger.info(f"[W{self.worker_id}] Ready.")
        self._task = asyncio.create_task(self._run_loop())

    async def _ensure_browser(self):
        """Pastikan browser berjalan, restart jika crash."""
        async with self._browser_lock:
            if self._browser is not None:
                try:
                    # Cek apakah browser masih hidup
                    await self._browser.contexts
                    return
                except Exception:
                    logger.warning(f"[W{self.worker_id}] Browser rusak, merestart...")
                    await self._close_browser()
            
            try:
                self._browser = await AsyncCamoufox(
                    headless=self.headless,
                    firefox_user_prefs=FIREFOX_PREFS,
                    os="windows",
                    humanize=True,
                    block_webrtc=True,
                    i_know_what_im_doing=True,
                    addons=[],
                    args=["--no-sandbox"],
                ).start()
                logger.info(f"[W{self.worker_id}] Browser restarted.")
            except Exception as e:
                logger.error(f"[W{self.worker_id}] Gagal memulai browser: {e}")
                raise

    async def _close_browser(self):
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

    async def close(self):
        self._is_closing = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._close_browser()
        logger.info(f"[W{self.worker_id}] Closed.")

    async def _run_loop(self):
        while not self._is_closing:
            try:
                job: SolveJob = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            
            try:
                result = await self._execute(job)
                job.future.set_result(result)
            except Exception as exc:
                job.future.set_exception(exc)
            finally:
                self.queue.task_done()

    async def _execute(self, job: SolveJob) -> TurnstileResult:
        start = time.time()
        page = None
        try:
            # Pastikan browser hidup
            await self._ensure_browser()

            total_timeout = job.timeout + 10
            page = await asyncio.wait_for(self._setup_page(job), timeout=total_timeout)
            
            token = await asyncio.wait_for(
                self._wait_for_token(page, job.timeout),
                timeout=job.timeout + 5
            )

            elapsed = round(time.time() - start, 3)

            if token:
                logger.info(f"[W{self.worker_id}] Solved in {elapsed}s")
                return TurnstileResult(token=token, elapsed=elapsed, status="completed")
            else:
                logger.error(f"[W{self.worker_id}] Timed out after {elapsed}s")
                return TurnstileResult(
                    token=None,
                    elapsed=elapsed,
                    status="failed",
                    error="Timed out waiting for Turnstile token",
                )

        except (asyncio.TimeoutError, asyncio.CancelledError):
            elapsed = round(time.time() - start, 3)
            logger.error(f"[W{self.worker_id}] Task timeout after {elapsed}s")
            return TurnstileResult(
                token=None,
                elapsed=elapsed,
                status="failed",
                error="Task execution timeout",
            )

        except Exception as exc:
            elapsed = round(time.time() - start, 3)
            error_msg = str(exc)
            logger.error(f"[W{self.worker_id}] Error: {error_msg}")
            
            # Jika browser crash, restart
            if "closed" in error_msg.lower() or "target page" in error_msg.lower():
                logger.warning(f"[W{self.worker_id}] Browser crash detected, restarting...")
                await self._close_browser()
            
            return TurnstileResult(
                token=None, elapsed=elapsed, status="failed", error=error_msg
            )

        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass

    async def _setup_page(self, job: SolveJob):
        url = job.url if job.url.endswith("/") else job.url + "/"

        attrs = f'data-sitekey="{job.sitekey}"'
        if job.action:
            attrs += f' data-action="{job.action}"'
        if job.cdata:
            attrs += f' data-cdata="{job.cdata}"'

        extra = ""
        if job.page_data:
            extra = f'<input type="hidden" name="chlPageData" value="{job.page_data}">'

        html = HTML_TEMPLATE.replace(
            "<!-- cf turnstile -->",
            f'<div class="cf-turnstile" {attrs}></div>{extra}',
        )

        # Browser harus hidup, tapi kita cek ulang
        await self._ensure_browser()
        
        page = await self._browser.new_page()

        async def handle_route(route):
            req = route.request
            req_url = req.url
            if req_url.rstrip("/") == url.rstrip("/"):
                await route.fulfill(
                    body=html,
                    status=200,
                    content_type="text/html; charset=utf-8",
                )
            elif any(h in req_url for h in ALLOWED_HOSTS):
                await route.continue_()
            else:
                await route.abort()

        await page.route("**/*", handle_route)
        await page.goto(url, wait_until="domcontentloaded")
        return page

    async def _wait_for_token(self, page, timeout: int) -> Optional[str]:
        try:
            await page.wait_for_function(
                """() => {
                    const el = document.querySelector('[name=cf-turnstile-response]');
                    return el && el.value !== '';
                }""",
                timeout=timeout * 1000,
                polling=100,
            )
            el = await page.query_selector("[name=cf-turnstile-response]")
            if el:
                token = await el.get_attribute("value")
                if token:
                    logger.info(f"[W{self.worker_id}] Token received: {token[:20]}...")
                    return token
        except Exception as e:
            logger.warning(f"[W{self.worker_id}] Error waiting for token: {e}")
        return None


class BrowserPool:
    def __init__(self, pool_size: int = 3, headless: bool = True):
        self.pool_size = pool_size
        self.headless = headless
        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: list[BrowserWorker] = []
        self._started = False

    async def start(self):
        if self._started:
            return
        logger.info(f"Starting {self.pool_size} browser workers...")
        workers = [
            BrowserWorker(worker_id=i + 1, queue=self._queue, headless=self.headless)
            for i in range(self.pool_size)
        ]
        await asyncio.gather(*[w.start() for w in workers])
        self._workers = workers
        self._started = True
        logger.info(f"All {self.pool_size} workers ready.")

    async def close(self):
        logger.info("Shutting down browser pool...")
        await asyncio.gather(*[w.close() for w in self._workers])
        self._workers.clear()
        self._started = False

    async def solve(
        self,
        url: str,
        sitekey: str,
        action: Optional[str] = None,
        cdata: Optional[str] = None,
        page_data: Optional[str] = None,
        timeout: int = 45,
    ) -> TurnstileResult:
        if not self._started:
            raise RuntimeError("BrowserPool.start() has not been called.")

        job = SolveJob(
            url=url, sitekey=sitekey, action=action,
            cdata=cdata, page_data=page_data, timeout=timeout,
        )
        await self._queue.put(job)
        depth = self._queue.qsize()
        if depth > 0:
            logger.info(f"Queued — {depth} job(s) waiting for a free worker.")

        return await job.future

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()
