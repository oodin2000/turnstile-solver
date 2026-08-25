"""
server.py — Async FastAPI server for solving Cloudflare Turnstile challenges.

Architecture:
  - On startup: launches a BrowserPool with 3 persistent Camoufox browsers.
  - POST /solve: enqueues a job, returns a taskId immediately.
  - GET /tasks/{taskId}: poll for result.
  - GET /health: live queue depth + worker count.
  - On shutdown: gracefully closes all browsers.

Run with:
    python server.py
"""
import os
import json
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.core.solver import TurnstileSolver, TurnstileResult
from src.core.logger import setup_logger

logger = setup_logger("API")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

POOL_SIZE = config.get("pool_size", 2)
HEADLESS = config.get("headless", True)
SOLVE_TIMEOUT = config.get("solve_timeout", 45)
HOST = config.get("host", "127.0.0.1")
PORT = config.get("port", 8080)

tasks: dict[str, dict] = {}

solver = TurnstileSolver(headless=HEADLESS, pool_size=POOL_SIZE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Turnstile Solver API — launching {POOL_SIZE} browsers...")
    await TurnstileSolver.start_pool(headless=HEADLESS, pool_size=POOL_SIZE)
    logger.info("Browser pool ready. API accepting requests.")
    yield
    logger.info("Shutting down — closing browser pool...")
    await TurnstileSolver.close_pool()
    logger.info("Done.")


app = FastAPI(
    title="Turnstile Solver API",
    description=(
        "Async Cloudflare Turnstile solver backed by a pool of "
        f"{POOL_SIZE} persistent browser instances."
    ),
    version="2.0.0",
    lifespan=lifespan,
)


class SolveRequest(BaseModel):
    sitekey: str = Field(..., description="Turnstile site key")
    site: str = Field(..., description="URL of the page with the Turnstile widget")
    pageAction: Optional[str] = Field(
        None, description="Action value passed to turnstile.render()"
    )
    data: Optional[str] = Field(None, description="Custom data value (cData)")
    pageData: Optional[str] = Field(
        None, description="Challenge page payload (chlPageData)"
    )
    timeout: Optional[int] = Field(
        SOLVE_TIMEOUT, description="Seconds to wait for a token before failing"
    )


class TaskResponse(BaseModel):
    taskId: str
    status: str
    token: Optional[str] = None
    error: Optional[str] = None
    elapsed: Optional[float] = None
    queueDepth: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    poolSize: int
    queueDepth: int
    activeTasks: int


async def _solve_task(task_id: str, request: SolveRequest):
    """Runs in the background; updates the task store when done."""
    logger.info(f"[{task_id}] Queued solve for {request.site}")
    try:
        result: TurnstileResult = await solver.solve(
            url=request.site,
            sitekey=request.sitekey,
            action=request.pageAction,
            cdata=request.data,
            page_data=request.pageData,
            timeout=request.timeout or SOLVE_TIMEOUT,
        )
        tasks[task_id].update(
            {
                "status": result.status,
                "token": result.token,
                "error": result.error,
                "elapsed": result.elapsed,
            }
        )
        if result.status == "completed":
            logger.info(f"[{task_id}] Solved in {result.elapsed}s")
        else:
            logger.error(f"[{task_id}] Failed after {result.elapsed}s — {result.error}")

    except Exception as exc:
        logger.error(f"[{task_id}] Unexpected error: {exc}")
        tasks[task_id].update(
            {
                "status": "failed",
                "token": None,
                "error": str(exc),
                "elapsed": None,
            }
        )


@app.post("/solve", response_model=TaskResponse, status_code=202)
async def create_solve_task(request: SolveRequest, background_tasks: BackgroundTasks):
    """
    Enqueue a Turnstile solve job.
    Returns immediately with a taskId; poll GET /tasks/{taskId} for the result.
    """
    task_id = uuid.uuid4().hex[:8]
    tasks[task_id] = {
        "status": "processing",
        "token": None,
        "error": None,
        "elapsed": None,
    }
    background_tasks.add_task(_solve_task, task_id, request)
    logger.info(f"[{task_id}] Task created for {request.site}")
    return TaskResponse(
        taskId=task_id,
        status="processing",
        queueDepth=solver.queue_size,
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """Poll the status of a previously submitted solve task."""
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return TaskResponse(
        taskId=task_id,
        status=task["status"],
        token=task.get("token"),
        error=task.get("error"),
        elapsed=task.get("elapsed"),
        queueDepth=solver.queue_size,
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Returns pool status and current queue depth."""
    return HealthResponse(
        status="ok",
        poolSize=POOL_SIZE,
        queueDepth=solver.queue_size,
        activeTasks=sum(1 for t in tasks.values() if t["status"] == "processing"),
    )


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """Remove a completed task from the in-memory store."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    del tasks[task_id]


if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    import uvicorn
    logger.info(f"Starting Turnstile Solver API on http://{HOST}:{PORT}")
    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="warning",
    )
