def pick_provider(model: str) -> str:
    """
    Minimal first routing rule:
    - For now every model goes to Gemini.
    - Later this function can choose provider by cost/latency/quality tiers.
    """
    _ = model
    return "gemini"
