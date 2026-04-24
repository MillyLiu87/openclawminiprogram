# openclaw_client.py — 对接 DeepSeek OpenAI-compatible API
#
# DeepSeek 是无状态的（不像 OpenClaw 会自动维护 session），
# 所以这里用内存字典按 openid 维护每个用户的多轮对话历史。

import httpx
import json
import logging
from typing import AsyncGenerator, Dict, List
from config import (
    DEEPSEEK_BASE_URL,
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    SYSTEM_PROMPT,
    HISTORY_MAX_MESSAGES,
)

logger = logging.getLogger(__name__)

CHAT_URL = f"{DEEPSEEK_BASE_URL}/chat/completions"

# openid → 对话历史（不含 system）
_histories: Dict[str, List[dict]] = {}


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }


def _get_messages(openid: str, user_message: str) -> List[dict]:
    history = _histories.setdefault(openid, [])
    history.append({"role": "user", "content": user_message})
    # 截断：保留最近 N 条
    if len(history) > HISTORY_MAX_MESSAGES:
        del history[: len(history) - HISTORY_MAX_MESSAGES]
    return [{"role": "system", "content": SYSTEM_PROMPT}] + history


def _append_assistant(openid: str, content: str):
    if not content:
        return
    history = _histories.setdefault(openid, [])
    history.append({"role": "assistant", "content": content})
    if len(history) > HISTORY_MAX_MESSAGES:
        del history[: len(history) - HISTORY_MAX_MESSAGES]


def reset_history(openid: str):
    _histories.pop(openid, None)


def _payload(openid: str, user_message: str, stream: bool) -> dict:
    return {
        "model": DEEPSEEK_MODEL,
        "messages": _get_messages(openid, user_message),
        "user": openid,
        "stream": stream,
    }


async def send_message(openid: str, message: str) -> str:
    """普通请求：等待完整回复后返回字符串。"""
    payload = _payload(openid, message, stream=False)
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(CHAT_URL, json=payload, headers=_headers())
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
            _append_assistant(openid, reply)
            return reply
    except httpx.HTTPStatusError as e:
        logger.error(f"DeepSeek HTTP {e.response.status_code}: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"DeepSeek error: {e}")
        raise


async def stream_message(openid: str, message: str) -> AsyncGenerator[str, None]:
    """流式请求：逐 chunk yield 文字内容，结束后把完整回复写回历史。"""
    payload = _payload(openid, message, stream=True)
    collected: List[str] = []
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", CHAT_URL, json=payload, headers=_headers()) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = line[6:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            collected.append(content)
                            yield content
                    except (json.JSONDecodeError, KeyError):
                        continue
        _append_assistant(openid, "".join(collected))
    except httpx.HTTPStatusError as e:
        logger.error(f"DeepSeek stream HTTP {e.response.status_code}")
        raise
    except Exception as e:
        logger.error(f"DeepSeek stream error: {e}")
        raise
