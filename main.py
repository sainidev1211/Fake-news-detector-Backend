"""
main.py — FastAPI application entry point.

Starts the SentinelLens Fake News Analyzer API backed by Groq Cloud.
"""
import os
import time
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # load .env BEFORE any service imports

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.analyze import router as analyze_router
from services.ai_service import MODEL
from utils.cache import cache
from utils.logger import get_logger, request_id_var

logger = get_logger("main")


# ── startup / shutdown ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        logger.error("GROQ_API_KEY is not set! Please create a .env file.")
    else:
        logger.info("SentinelLens API started — model=%s", MODEL)
    yield
    logger.info("SentinelLens API shutting down.")


# ── app factory ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SentinelLens — Fake News Analyzer API",
    description="AI-powered misinformation detection using Groq Cloud + Wikipedia.",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request-ID + latency middleware ───────────────────────────────────────────

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    rid = str(uuid.uuid4())[:8]
    request_id_var.set(rid)          # inject into context for logging

    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed = int((time.perf_counter() - t0) * 1000)

    response.headers["X-Request-ID"] = rid
    response.headers["X-Response-Time"] = f"{elapsed}ms"

    logger.info("%s %s → %d (%dms)", request.method, request.url.path, response.status_code, elapsed)
    return response


# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(analyze_router, tags=["Analysis"])


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    api_key_set = bool(os.environ.get("GROQ_API_KEY", ""))
    return {
        "status": "ok" if api_key_set else "error",
        "provider": "Groq Cloud",
        "model": MODEL,
        "api_key_configured": api_key_set,
        "cached_entries": cache.size(),
    }


# ── Catch-all error handler ────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error. Please try again."},
    )


# ── Dev entrypoint ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
