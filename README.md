# Aura-Link

A multi-LLM gateway that sits between your application and multiple AI providers. Instead of hardcoding a single model, requests route through Aura-Link which selects the best provider based on cost, speed, and complexity — then logs everything so you can see exactly what you're spending and how each model is performing.

## Why Aura-Link

Most apps are locked into one AI provider. Switching models means rewriting code. Aura-Link abstracts that away — your app talks to one API, Aura-Link handles the rest. It also gives you visibility that the providers don't — token usage, cost per request, and model performance in one dashboard.

## Architecture
```
Client Request
      ↓
Aura-Link Gateway (FastAPI)
      ↓
Routing Engine — picks provider based on cost/complexity
      ↓
┌─────────────┬─────────────┬─────────────┐
│   OpenAI    │  Azure AI   │ Local Model │
└─────────────┴─────────────┴─────────────┘
      ↓
Response + usage logged to PostgreSQL
      ↓
Dashboard (Next.js) — real time token usage, cost, performance
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| Cache | Redis |
| Observability | OpenTelemetry |
| Infrastructure | Docker, Docker Compose |

## Features

- Intelligent routing across multiple LLM providers
- Real time cost and token usage tracking
- Provider performance monitoring
- Single unified API for your application
- Dashboard with live metrics

## Status

🚧 Active development — backend gateway and routing engine in progress.

## Getting Started
```bash
# Clone the repo
git clone https://github.com/ms-977/aura-link.git
cd aura-link

# Start the backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your Gemini API key
cp .env.example .env
set -a
source .env
set +a

# Run API
uvicorn main:app --reload

# API docs available at
http://127.0.0.1:8000/docs
```

## First API Call

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.0-flash",
    "messages": [
      {"role": "user", "content": "Give me one sentence about Aura-Link."}
    ],
    "temperature": 0.7
  }'
```

## Gemini -> Local Fallback (Ollama)

Aura-Link now uses Gemini as the primary provider and can automatically fall back to a local Ollama model when Gemini fails (for example on quota/rate limits).

1. Install Ollama and pull a small model:

```bash
ollama pull qwen2.5:3b
```

2. Keep these values in `backend/.env`:

```env
ENABLE_LOCAL_FALLBACK=true
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

3. Run the same `/v1/chat/completions` request. If Gemini returns 429/5xx, Aura-Link will return a response from local Ollama instead.