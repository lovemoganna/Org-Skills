#!/usr/bin/env python3
"""Unified LLM client for note-reforge evaluations.

Uses GROQ_API_KEY with pinned model 'openai/gpt-oss-120b'.
Supports automatic retry on rate limits (429), temperature=0.0, timing, token count tracking.
"""
from __future__ import annotations

import os
import re
import time
from typing import Any
import requests

DEFAULT_MODEL = "openai/gpt-oss-120b"
API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_llm(
    prompt: str,
    system_prompt: str | None = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    max_tokens: int = 4096,
    timeout: int = 90,
    max_retries: int = 5
) -> dict[str, Any]:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    start_time = time.time()
    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                elapsed = time.time() - start_time
                data = resp.json()
                choice = data["choices"][0]
                usage = data.get("usage", {})
                return {
                    "content": choice["message"]["content"],
                    "finish_reason": choice.get("finish_reason"),
                    "latency_sec": round(elapsed, 3),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "model": model
                }
            elif resp.status_code == 429:
                # Rate limit encountered - parse retry time
                wait_sec = 6.0
                err_text = resp.text
                m = re.search(r"try again in ([\d\.]+)s", err_text)
                if m:
                    wait_sec = float(m.group(1)) + 1.0
                print(f"    [Rate limit 429] Waiting {wait_sec:.1f}s before retry (attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_sec)
                continue
            else:
                raise RuntimeError(f"LLM API Call failed ({resp.status_code}): {resp.text}")
        except requests.exceptions.RequestException as exc:
            if attempt < max_retries - 1:
                print(f"    [Network error] {exc}, retrying in 3s...")
                time.sleep(3.0)
            else:
                raise

    raise RuntimeError(f"LLM API Call failed after {max_retries} retries due to rate limits.")

if __name__ == "__main__":
    res = call_llm("Answer with only: PING_OK")
    print("Test Call Result:", res)
