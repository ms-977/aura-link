import json
from typing import Any, Optional

import httpx 


from schemas.chat import ChatCompletionRequest


class ProviderError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GeminiAdapter:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def create_chat_completion(self, payload: ChatCompletionRequest) -> dict[str, Any]:
        endpoint = f"{self.base_url}/{payload.model}:generateContent"
        params = {"key": self.api_key}
        body = self._to_gemini_payload(payload)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(endpoint, params=params, json=body)

        if response.status_code >= 400:
            raise ProviderError(
                f"Gemini request failed: {response.status_code} {self._safe_text(response)}",
                status_code=response.status_code,
            )

        gemini_data = response.json()
        return self._to_openai_compatible(payload.model, gemini_data)

    def _to_gemini_payload(self, payload: ChatCompletionRequest) -> dict[str, Any]:
        contents = []
        for msg in payload.messages:
            role = "model" if msg.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

        generation_config: dict[str, Any] = {}
        if payload.temperature is not None:
            generation_config["temperature"] = payload.temperature
        if payload.max_tokens is not None:
            generation_config["maxOutputTokens"] = payload.max_tokens

        data: dict[str, Any] = {"contents": contents}
        if generation_config:
            data["generationConfig"] = generation_config
        return data

    def _to_openai_compatible(self, model: str, gemini_data: dict[str, Any]) -> dict[str, Any]:
        text = ""
        candidates = gemini_data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))

        usage_metadata = gemini_data.get("usageMetadata", {})
        prompt_tokens = usage_metadata.get("promptTokenCount")
        completion_tokens = usage_metadata.get("candidatesTokenCount")
        total_tokens = usage_metadata.get("totalTokenCount")

        return {
            "id": gemini_data.get("responseId", "gemini-response"),
            "object": "chat.completion",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": self._extract_finish_reason(candidates),
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
            "raw_provider_response": gemini_data,
        }

    def _extract_finish_reason(self, candidates: list[dict[str, Any]]) -> Optional[str]:
        if not candidates:
            return None
        reason = candidates[0].get("finishReason")
        if not reason:
            return None
        return str(reason).lower()

    def _safe_text(self, response: httpx.Response) -> str:
        try:
            return json.dumps(response.json())
        except json.JSONDecodeError:
            return response.text
