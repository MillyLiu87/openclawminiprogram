# session_manager.py — 轻量活跃度追踪
#
# OpenClaw 通过 user=openid 自动维护每用户独立 session，
# 本地无需创建/管理 session，只追踪活跃时间（用于统计/清理）。

import time
import logging
from typing import Dict
from config import SESSION_TTL

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self):
        # openid → last_active timestamp
        self._active: Dict[str, float] = {}

    def touch(self, openid: str):
        """标记用户活跃"""
        self._active[openid] = time.time()

    def cleanup(self):
        """清理长期不活跃的记录"""
        now = time.time()
        expired = [oid for oid, t in self._active.items() if now - t > SESSION_TTL]
        for oid in expired:
            del self._active[oid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} inactive sessions")

    @property
    def active_count(self) -> int:
        return len(self._active)


# 单例
session_manager = SessionManager()
