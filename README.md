# WeChat Mini Program ↔ OpenClaw Bridge

微信小程序接入 OpenClaw，实现多用户独立 AI 对话。

## 目录结构

```
wechat-openclaw/
├── backend/                 # FastAPI 后端（部署在 VPS）
│   ├── config.py            # ⭐ 所有配置在这里
│   ├── main.py              # 入口、路由
│   ├── openclaw_client.py   # OpenClaw API 封装（接口变了只改这里）
│   ├── session_manager.py   # 每用户独立 session 管理
│   ├── ws_manager.py        # WebSocket 连接管理
│   ├── .env.example         # 环境变量模板
│   └── requirements.txt
└── miniprogram/             # 微信小程序前端
    ├── utils/
    │   ├── config.js        # ⭐ 小程序配置（后端地址等）
    │   └── ws.js            # WebSocket 封装（含自动重连）
    └── pages/chat/
        ├── chat.js          # 页面逻辑
        ├── chat.wxml        # 聊天 UI
        └── chat.wxss        # 样式

```

## 核心设计

### 多用户隔离
每个微信用户通过 `openid` 标识，拥有独立的 OpenClaw Session：
```
用户A openid → session_key_A → 独立对话上下文
用户B openid → session_key_B → 独立对话上下文
```

### 修改配置
- **后端**：修改 `backend/config.py` 或设置环境变量
- **小程序**：修改 `miniprogram/utils/config.js`

### 修改 OpenClaw 接入方式
只需修改 `backend/openclaw_client.py` 中的两个函数：
- `create_session()` — 如何创建用户 session
- `send_message()` — 如何发送消息并获取回复

## 启动后端

```bash
cd backend
cp .env.example .env
# 编辑 .env 填写实际值

pip install -r requirements.txt
python main.py
# 或: uvicorn main:app --host 0.0.0.0 --port 8000
```

## 小程序开发

1. 下载微信开发者工具
2. 导入 `miniprogram/` 目录
3. 修改 `utils/config.js` 中的后端地址
4. 工具栏 → 详情 → 本地设置 → **勾选「不校验域名」**（开发阶段）

## 待实现

- [ ] 确认 OpenClaw API 接口格式，完善 `openclaw_client.py`
- [ ] 消息历史持久化（当前重启后清空）
- [ ] 用户头像（接入微信用户信息）
- [ ] 流式输出（Streaming）支持
