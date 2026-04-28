"""
services/ai_service.py — Groq Cloud inference for Fake News Detection.

Uses the Groq Python SDK (OpenAI-compatible) with llama-3.3-70b-versatile.
Raises RuntimeError on failure so callers can return clean error responses.
"""
import json
import os
import re
from groq import Groq, APIError, APIConnectionError, RateLimitError
from utils.logger import get_logger

logger = get_logger("ai_service")

# ── Groq client (initialised once at import time) ─────────────────────────────
_client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2
MAX_TOKENS = 1024

# ── System prompt ─────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are an advanced Fake News Detection AI.

Analyze the given news content and classify it as REAL, FAKE, or MISLEADING.

Follow this process:
1. Summarize the claim in one sentence.
2. Verify facts using general knowledge and any provided Wikipedia context.
3. Detect red flags: clickbait, emotional tone, missing sources, exaggeration, conspiracy language.
4. Estimate source credibility.
5. Provide a final verdict (REAL, FAKE, or MISLEADING).
6. Provide a confidence score from 0 to 100.

Return STRICT JSON — no extra text, no markdown fences:
{
  "claim_summary": "...",
  "verdict": "REAL | FAKE | MISLEADING",
  "confidence": 0-100,
  "red_flags": ["...", "..."],
  "explanation": "...",
  "suggested_verification_sources": ["Wikipedia", "Google News"]
}"""


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from raw LLM output."""
    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).strip("`").strip()

    # Find first {...} block
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    return json.loads(text)


def _normalise(raw: dict) -> dict:
    """Ensure required fields exist with correct types."""
    verdict = str(raw.get("verdict", "MISLEADING")).upper()
    if verdict not in ("REAL", "FAKE", "MISLEADING"):
        verdict = "MISLEADING"

    confidence = raw.get("confidence", 50)
    try:
        confidence = max(0, min(100, int(float(confidence))))
    except (TypeError, ValueError):
        confidence = 50

    red_flags = raw.get("red_flags", [])
    if not isinstance(red_flags, list):
        red_flags = [str(red_flags)]

    sources = raw.get("suggested_verification_sources", ["Wikipedia", "Google News"])
    if not isinstance(sources, list):
        sources = [str(sources)]

    return {
        "claim_summary": str(raw.get("claim_summary", "")).strip() or "No summary provided.",
        "verdict": verdict,
        "confidence": confidence,
        "red_flags": red_flags,
        "explanation": str(raw.get("explanation", "")).strip() or "No explanation provided.",
        "suggested_verification_sources": sources,
    }


async def run_inference(content: str, wiki_context: str | None = None) -> dict:
    """
    Send content (and optional Wikipedia context) to Groq and return
    a normalised result dict.

    Raises RuntimeError on any failure.
    """
    user_msg = content.strip()
    if wiki_context:
        user_msg = (
            f"[External Verification Context from Wikipedia]\n{wiki_context}\n\n"
            f"[News Content to Analyze]\n{user_msg}"
        )

    logger.info("Sending %d chars to Groq (%s)", len(user_msg), MODEL)
    try:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            timeout=30,
        )
    except RateLimitError:
        raise RuntimeError("Groq rate limit reached. Please wait a moment and try again.")
    except APIConnectionError:
        raise RuntimeError("Cannot connect to Groq API. Check your internet connection.")
    except APIError as exc:
        raise RuntimeError(f"Groq API error: {exc.message}")
    except Exception as exc:
        raise RuntimeError(f"Unexpected error calling Groq: {exc}")

    raw_text = response.choices[0].message.content or ""
    logger.debug("Groq raw response: %s", raw_text[:300])

    try:
        raw_dict = _extract_json(raw_text)
    except json.JSONDecodeError:
        logger.error("JSON parse failed. Raw: %s", raw_text[:400])
        raise RuntimeError(
            f"Model returned invalid JSON. Raw snippet: {raw_text[:200]}"
        )

    return _normalise(raw_dict)
