# openclaw_client.py — 对接 OpenClaw OpenAI-compatible API
#
# 核心原理：
#   POST /v1/chat/completions  with  user=openid
#   → OpenClaw 自动为每个 user 维护独立 session，天然多用户隔离
#   → 无需手动创建 / 管理 session

import httpx
import json
import logging
from typing import AsyncGenerator
from config import OPENCLAW_BASE_URL, OPENCLAW_TOKEN, OPENCLAW_AGENT_ID

logger = logging.getLogger(__name__)

CHAT_URL = f"{OPENCLAW_BASE_URL}/v1/chat/completions"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {OPENCLAW_TOKEN}",
        "Content-Type": "application/json",
        "x-openclaw-agent-id": OPENCLAW_AGENT_ID,
    }


def _payload(openid: str, message: str, stream: bool = False) -> dict:
    return {
        "model": "openclaw",
        "messages": [{"role": "user", "content": message}],
        "user": openid,          # ← 关键：OpenClaw 用这个字段隔离 session
        "stream": stream,
    }


async def send_message(openid: str, message: str) -> str:
    """
    普通请求：等待完整回复后返回字符串。
    适合 HTTP /chat 接口。
    """
    payload = _payload(openid, message, stream=False)
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(CHAT_URL, json=payload, headers=_headers())
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenClaw HTTP {e.response.status_code}: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"OpenClaw error: {e}")
        raise


async def stream_message(openid: str, message: str) -> AsyncGenerator[str, None]:
    """
    流式请求：逐 chunk yield 文字内容。
    适合 WebSocket 实时输出（边生成边推送给用户）。

    用法：
        async for chunk in openclaw_client.stream_message(openid, msg):
            await ws_manager.send(openid, {"type": "chunk", "content": chunk})
    """
    payload = _payload(openid, message, stream=True)
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
                            yield content
                    except (json.JSONDecodeError, KeyError):
                        continue
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenClaw stream HTTP {e.response.status_code}")
        raise
    except Exception as e:
        logger.error(f"OpenClaw stream error: {e}")
        raise
