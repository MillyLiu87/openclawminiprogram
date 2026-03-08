# ws_manager.py — WebSocket 连接管理（每个用户独立连接）
import logging
from typing import Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # openid → WebSocket
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, openid: str, ws: WebSocket):
        await ws.accept()
        # 如果该用户已有旧连接，先关掉（同一用户多端只保留最新）
        if openid in self._connections:
            try:
                await self._connections[openid].close()
            except Exception:
                pass
        self._connections[openid] = ws
        logger.info(f"WebSocket connected: {openid} (total: {len(self._connections)})")

    def disconnect(self, openid: str):
        if openid in self._connections:
            del self._connections[openid]
            logger.info(f"WebSocket disconnected: {openid}")

    async def send(self, openid: str, data: dict):
        """向指定用户推送消息"""
        ws = self._connections.get(openid)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"Send failed for {openid}: {e}")
                self.disconnect(openid)

    async def broadcast(self, data: dict):
        """广播（调试用，正常业务不用）"""
        for openid, ws in list(self._connections.items()):
            await self.send(openid, data)

    @property
    def active_count(self) -> int:
        return len(self._connections)


# 单例
ws_manager = ConnectionManager()
