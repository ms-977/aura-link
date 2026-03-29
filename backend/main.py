import logging
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from config import Settings
from providers.gemini_adapter import GeminiAdapter, ProviderError
from providers.ollama_adapter import OllamaAdapter
from routing.engine import pick_provider
from schemas.chat import ChatCompletionRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aura-link")

app = FastAPI(title="Aura-Link", description="Multi-LLM Gateway API")
settings = Settings()


@app.get("/")
def root():
    return {"message": "Aura-Link is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/v1/chat/completions")
async def chat_completions(payload: ChatCompletionRequest):
    request_id = f"req_{uuid.uuid4().hex}"
    started_at = time.perf_counter()

    provider_name = pick_provider(payload.model)
    if provider_name != "gemini":
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider_name}")

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
        logger.info(
            "chat_completion request_id=%s provider=%s model=%s latency_ms=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
            request_id,
            "ollama",
            payload.model,
            latency_ms,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
            usage.get("total_tokens"),
        )
        return JSONResponse(content=response_payload, headers={"X-Request-Id": request_id})

    adapter = GeminiAdapter(api_key=settings.gemini_api_key)

    try:
        response_payload = await adapter.create_chat_completion(payload)
    except ProviderError as exc:
        should_fallback = settings.enable_local_fallback and exc.status_code in {429, 500, 502, 503}
        if not should_fallback:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        logger.warning(
            "gemini_failed request_id=%s reason=%s; falling_back_to=ollama model=%s",
            request_id,
            str(exc),
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
                detail=f"Primary and fallback providers failed. Gemini: {exc}. Ollama: {fallback_exc}",
            ) from fallback_exc
        provider_name = "ollama"

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    usage = response_payload.get("usage", {})

    logger.info(
        "chat_completion request_id=%s provider=%s model=%s latency_ms=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
        request_id,
        provider_name,
        payload.model,
        latency_ms,
        usage.get("prompt_tokens"),
        usage.get("completion_tokens"),
        usage.get("total_tokens"),
    )

    return JSONResponse(content=response_payload, headers={"X-Request-Id": request_id})