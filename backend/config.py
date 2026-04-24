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

# ─── DeepSeek 连接配置 ────────────────────────────────────────────
# DeepSeek 使用 OpenAI-compatible API
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY  = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL    = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 系统提示词（可选）
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "你是一个乐于助人的 AI 助手。")

# 每个用户保留的对话历史最大条数（user+assistant 合计）
HISTORY_MAX_MESSAGES = int(os.getenv("HISTORY_MAX_MESSAGES", "20"))

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
