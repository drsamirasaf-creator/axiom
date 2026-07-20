"""Thin Anthropic Messages API client (ADR-006 §1).

The single seam between AXIOM and the model: tests monkeypatch complete();
production requires ANTHROPIC_API_KEY. Everything downstream of this call
is deterministic validation — the model proposes, the gates dispose.
"""
import httpx
from ...core.config import anthropic_api_key, ai_model

API_URL = "https://api.anthropic.com/v1/messages"


class AINotConfigured(RuntimeError):
    pass


def complete(system: str, user_text: str, max_tokens: int = 2000) -> str:
    key = anthropic_api_key()
    if not key:
        raise AINotConfigured(
            "ANTHROPIC_API_KEY is not configured; AI document analysis is "
            "unavailable in this deployment")
    resp = httpx.post(API_URL, timeout=90.0, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01",
        "content-type": "application/json"},
        json={"model": ai_model(), "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": user_text}],
              "system": system})
    resp.raise_for_status()
    data = resp.json()
    return "".join(b.get("text", "") for b in data.get("content", [])
                   if b.get("type") == "text")


def complete_messages(system: str, messages: list, max_tokens: int = 1500,
                      model: str | None = None) -> tuple[str, dict]:
    """Multi-turn variant used by Prescience (Ask AXIOM). Unlike complete(), it
    takes a full messages array (conversation history) and returns BOTH the text
    and the usage dict {input_tokens, output_tokens} so callers can meter cost.
    Raises AINotConfigured when the key is absent (caller maps to a 503)."""
    key = anthropic_api_key()
    if not key:
        raise AINotConfigured(
            "Prescience is not configured; ANTHROPIC_API_KEY is unset in this "
            "deployment")
    resp = httpx.post(API_URL, timeout=90.0, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01",
        "content-type": "application/json"},
        json={"model": model or ai_model(), "max_tokens": max_tokens,
              "system": system, "messages": messages})
    resp.raise_for_status()
    data = resp.json()
    text = "".join(b.get("text", "") for b in data.get("content", [])
                   if b.get("type") == "text")
    usage = data.get("usage", {}) or {}
    return text, {"input_tokens": usage.get("input_tokens", 0),
                  "output_tokens": usage.get("output_tokens", 0)}
