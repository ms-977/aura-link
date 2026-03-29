from typing import Any, Optional, Tuple

import httpx

from providers.gemini_adapter import ProviderError
from schemas.chat import ChatCompletionRequest


class OllamaAdapter:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def create_chat_completion(self, payload: ChatCompletionRequest) -> dict[str, Any]:
        endpoint = f"{self.base_url}/api/chat"
        body = {
            "model": self.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in payload.messages],
            "stream": False,
            "options": self._options(payload),
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(endpoint, json=body)

        if response.status_code >= 400:
            raise ProviderError(
                f"Ollama request failed: {response.status_code} {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        text = data.get("message", {}).get("content", "")
        prompt_tokens, completion_tokens, total_tokens = self._extract_usage(data)

        return {
            "id": data.get("created_at", "ollama-response"),
            "object": "chat.completion",
            "model": self.model,
            "provider": "ollama",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop" if data.get("done") else None,
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
            "raw_provider_response": data,
        }

    def _options(self, payload: ChatCompletionRequest) -> dict[str, Any]:
        options: dict[str, Any] = {}
        if payload.temperature is not None:
            options["temperature"] = payload.temperature
        if payload.max_tokens is not None:
            options["num_predict"] = payload.max_tokens
        return options

    def _extract_usage(self, data: dict[str, Any]) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        prompt = data.get("prompt_eval_count")
        completion = data.get("eval_count")
        if prompt is None and completion is None:
            return None, None, None
        total = (prompt or 0) + (completion or 0)
        return prompt, completion, total
