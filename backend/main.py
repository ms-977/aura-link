from fastapi import FastAPI

app = FastAPI(title="Aura-Link", description="Multi-LLM Gateway API")

@app.get("/")
def root():
    return {"message": "Aura-Link is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}