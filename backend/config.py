import os


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip()
        self.enable_local_fallback = (
            os.getenv("ENABLE_LOCAL_FALLBACK", "true").strip().lower() == "true"
        )
