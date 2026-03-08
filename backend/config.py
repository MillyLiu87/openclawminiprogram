# config.py — 所有可配置项集中在这里
# 优先读环境变量，fallback 到默认值
import os
from pathlib import Path

# 自动加载同目录的 .env 文件
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ─── OpenClaw 连接配置 ────────────────────────────────────────────
OPENCLAW_HOST     = os.getenv("OPENCLAW_HOST", "localhost")
OPENCLAW_PORT     = int(os.getenv("OPENCLAW_PORT", "18789"))
OPENCLAW_BASE_URL = os.getenv("OPENCLAW_BASE_URL", f"http://localhost:18789")

# Gateway Bearer Token（openclaw.json → gateway.auth.token）
OPENCLAW_TOKEN    = os.getenv("OPENCLAW_TOKEN", "")

# 用哪个 Agent 回答小程序用户（可改成任意 agent id）
OPENCLAW_AGENT_ID = os.getenv("OPENCLAW_AGENT_ID", "main")

# ─── 后端服务配置 ─────────────────────────────────────────────────
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# ─── 微信配置 ─────────────────────────────────────────────────────
WX_APPID  = os.getenv("WX_APPID",  "your_appid_here")
WX_SECRET = os.getenv("WX_SECRET", "your_secret_here")

# ─── Session 配置 ─────────────────────────────────────────────────
# OpenClaw 通过 user 字段自动隔离 session，这里只是本地活跃度追踪
SESSION_TTL = int(os.getenv("SESSION_TTL", str(60 * 60 * 24)))  # 24 小时

# ─── 日志 ────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
