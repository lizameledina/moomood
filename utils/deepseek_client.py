from __future__ import annotations

from typing import Any, Dict, List, Optional

import aiohttp


def _build_chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


async def chat_completions(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout_s: int = 20,
    temperature: float = 0.6,
    max_tokens: int = 250,
) -> str:
    url = _build_chat_completions_url(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    timeout = aiohttp.ClientTimeout(total=timeout_s)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            data: Optional[Dict[str, Any]] = None
            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                raise RuntimeError(f"DeepSeek HTTP {resp.status}: {text}")

            if resp.status >= 400:
                raise RuntimeError(f"DeepSeek HTTP {resp.status}: {data}")

            try:
                return str(data["choices"][0]["message"]["content"]).strip()
            except Exception:
                raise RuntimeError(f"Unexpected DeepSeek response: {data}")

