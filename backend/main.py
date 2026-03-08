# main.py — FastAPI 入口
import logging
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import BACKEND_HOST, BACKEND_PORT, WX_APPID, WX_SECRET, LOG_LEVEL
from ws_manager import ws_manager
from session_manager import session_manager
import openclaw_client

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="WeChat-OpenClaw Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── 数据模型 ──────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    code: str

class LoginResponse(BaseModel):
    openid: str

class MessageRequest(BaseModel):
    openid: str
    message: str

class MessageResponse(BaseModel):
    reply: str


# ─── 微信登录 ──────────────────────────────────────────────────────

@app.post("/auth/wx_login", response_model=LoginResponse)
async def wx_login(req: LoginRequest):
    """用微信 code 换取 openid（每个用户唯一 ID）"""
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": WX_APPID,
        "secret": WX_SECRET,
        "js_code": req.code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if "openid" not in data:
        raise HTTPException(status_code=401, detail=f"微信登录失败: {data}")

    openid = data["openid"]
    session_manager.touch(openid)
    logger.info(f"User logged in: {openid}")
    return LoginResponse(openid=openid)


# ─── HTTP 聊天（简单轮询备用） ─────────────────────────────────────

@app.post("/chat", response_model=MessageResponse)
async def chat(req: MessageRequest):
    """HTTP 方式，等待完整回复。WebSocket 不可用时的降级方案。"""
    session_manager.touch(req.openid)
    reply = await openclaw_client.send_message(req.openid, req.message)
    return MessageResponse(reply=reply)


# ─── WebSocket 聊天（流式，推荐） ─────────────────────────────────

@app.websocket("/ws/{openid}")
async def websocket_chat(websocket: WebSocket, openid: str):
    """
    每个用户独立 WebSocket 连接，流式推送 AI 回复。

    客户端发送格式：{"message": "你好"}

    服务端推送格式：
      {"type": "typing"}               ← AI 开始处理
      {"type": "chunk",  "content": "..."} ← 流式文字片段
      {"type": "done"}                 ← 本轮回复结束
      {"type": "error",  "content": "..."} ← 出错
    """
    await ws_manager.connect(openid, websocket)
    session_manager.touch(openid)

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            session_manager.touch(openid)

            # 告知客户端 AI 开始处理
            await ws_manager.send(openid, {"type": "typing"})

            try:
                # 流式逐 chunk 推送
                async for chunk in openclaw_client.stream_message(openid, user_message):
                    await ws_manager.send(openid, {
                        "type": "chunk",
                        "content": chunk,
                    })

                # 本轮结束信号
                await ws_manager.send(openid, {"type": "done"})

            except Exception as e:
                logger.error(f"Error for {openid}: {e}")
                await ws_manager.send(openid, {
                    "type": "error",
                    "content": "处理消息时出错，请稍后重试",
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(openid)


# ─── 状态接口 ──────────────────────────────────────────────────────

@app.get("/status")
async def status():
    session_manager.cleanup()
    return {
        "status": "ok",
        "active_ws_connections": ws_manager.active_count,
        "active_sessions": session_manager.active_count,
    }


# ─── 启动 ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
