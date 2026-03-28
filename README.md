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
pip install fastapi uvicorn
uvicorn main:app --reload

# API docs available at
http://127.0.0.1:8000/docs
```