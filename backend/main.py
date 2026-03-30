import logging
import time
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import Settings
from providers.gemini_adapter import GeminiAdapter, ProviderError
from providers.ollama_adapter import OllamaAdapter
from routing.engine import pick_provider
from schemas.chat import ChatCompletionRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aura-link")

app = FastAPI(title="Aura-Link", description="Multi-LLM Gateway API")

# Allow the Next.js dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = Settings()

# ---------------------------------------------------------------------------
# In-memory request log — replaced by PostgreSQL in a later milestone
# ---------------------------------------------------------------------------
_request_log: List[Dict[str, Any]] = []

def _log_request(
    *,
    request_id: str,
    provider: str,
    model: str,
    latency_ms: int,
    prompt_tokens: Optional[int],
    completion_tokens: Optional[int],
    total_tokens: Optional[int],
) -> None:
    _request_log.append(
        {
            "request_id": request_id,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens or 0,
            "completion_tokens": completion_tokens or 0,
            "total_tokens": total_tokens or 0,
            "timestamp": time.time(),
        }
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "Aura-Link is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/v1/stats")
def stats():
    """Aggregate metrics from the in-memory request log."""
    total_requests = len(_request_log)
    total_tokens = sum(r["total_tokens"] for r in _request_log)

    # Per-provider breakdown
    per_provider: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"requests": 0, "total_tokens": 0, "total_latency_ms": 0}
    )
    for r in _request_log:
        p = per_provider[r["provider"]]
        p["requests"] += 1
        p["total_tokens"] += r["total_tokens"]
        p["total_latency_ms"] += r["latency_ms"]

    providers = []
    for name, data in per_provider.items():
        avg_latency = (
            round(data["total_latency_ms"] / data["requests"])
            if data["requests"]
            else 0
        )
        providers.append(
            {
                "name": name,
                "requests": data["requests"],
                "total_tokens": data["total_tokens"],
                "avg_latency_ms": avg_latency,
            }
        )

    return {
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "providers": providers,
    }


@app.post("/v1/chat/completions")
async def chat_completions(payload: ChatCompletionRequest):
    request_id = f"req_{uuid.uuid4().hex}"
    started_at = time.perf_counter()

    provider_name = pick_provider(payload.model)
    if provider_name != "gemini":
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider_name}")

    # ── No Gemini key → go straight to Ollama ──────────────────────────────
    if not settings.gemini_api_key:
        if not settings.enable_local_fallback:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is not set and local fallback is disabled.",
            )
        logger.warning(
            "gemini_key_missing request_id=%s; falling_back_to=ollama model=%s",
            request_id,
            settings.ollama_model,
        )
        ollama_adapter = OllamaAdapter(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
        try:
            response_payload = await ollama_adapter.create_chat_completion(payload)
        except ProviderError as fallback_exc:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini key missing and fallback provider failed: {fallback_exc}",
            ) from fallback_exc

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        usage = response_payload.get("usage", {})
        _log_request(
            request_id=request_id,
            provider="ollama",
            model=payload.model,
            latency_ms=latency_ms,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )
        logger.info(
            "chat_completion request_id=%s provider=ollama model=%s latency_ms=%s",
            request_id, payload.model, latency_ms,
        )
        return JSONResponse(content=response_payload, headers={"X-Request-Id": request_id})

    # ── Try Gemini, fall back to Ollama on quota/server errors ─────────────
    adapter = GeminiAdapter(api_key=settings.gemini_api_key)

    try:
        response_payload = await adapter.create_chat_completion(payload)
        provider_name = "gemini"
    except ProviderError as exc:
        should_fallback = settings.enable_local_fallback and exc.status_code in {429, 500, 502, 503}
        if not should_fallback:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        logger.warning(
            "gemini_failed request_id=%s reason=%s; falling_back_to=ollama model=%s",
            request_id, str(exc), settings.ollama_model,
        )
        ollama_adapter = OllamaAdapter(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
        try:
            response_payload = await ollama_adapter.create_chat_completion(payload)
            provider_name = "ollama"
        except ProviderError as fallback_exc:
            raise HTTPException(
                status_code=502,
                detail=f"Primary and fallback providers failed. Gemini: {exc}. Ollama: {fallback_exc}",
            ) from fallback_exc

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    usage = response_payload.get("usage", {})
    _log_request(
        request_id=request_id,
        provider=provider_name,
        model=payload.model,
        latency_ms=latency_ms,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
    )
    logger.info(
        "chat_completion request_id=%s provider=%s model=%s latency_ms=%s",
        request_id, provider_name, payload.model, latency_ms,
    )
    return JSONResponse(content=response_payload, headers={"X-Request-Id": request_id})