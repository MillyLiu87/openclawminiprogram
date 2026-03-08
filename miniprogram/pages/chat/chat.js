// pages/chat/chat.js
const Config = require('../../utils/config');
const WsClient = require('../../utils/ws');

Page({
  data: {
    messages: [],       // [{id, role:'user'|'ai', content:''}]
    inputText: '',
    isTyping: false,
    connected: false,
    openid: '',
    scrollToId: '',
  },

  _ws: null,
  _streamingMsgId: null,   // 当前正在流式输出的消息 id

  // ─── 生命周期 ──────────────────────────────────────────────────

  onLoad() {
    this._login();
  },

  onUnload() {
    this._ws && this._ws.close();
  },

  // ─── 微信登录 ─────────────────────────────────────────────────

  _login() {
    // 开发模式：跳过 wx.login，直接用固定 openid
    if (Config.DEV_MODE) {
      const openid = Config.DEV_OPENID;
      this.setData({ openid });
      this._connectWs(openid);
      return;
    }

    wx.login({
      success: (res) => {
        wx.request({
          url: Config.BACKEND_HTTP + Config.API.LOGIN,
          method: 'POST',
          data: { code: res.code },
          success: (r) => {
            const { openid } = r.data;
            this.setData({ openid });
            this._connectWs(openid);
          },
          fail: () => wx.showToast({ title: '登录失败，请重试', icon: 'none' }),
        });
      },
    });
  },

  // ─── WebSocket ────────────────────────────────────────────────

  _connectWs(openid) {
    this._ws = new WsClient({
      openid,
      onConnect:    () => this.setData({ connected: true }),
      onDisconnect: () => this.setData({ connected: false }),
      onMessage:    (data) => this._handleServerMessage(data),
    });
    this._ws.connect();
  },

  // ─── 处理服务端推送 ────────────────────────────────────────────
  //
  // 消息类型：
  //   typing  → AI 开始处理，显示 loading 气泡
  //   chunk   → 流式文字片段，追加到当前 AI 消息
  //   done    → 本轮结束，清除 loading 状态
  //   error   → 出错提示

  _handleServerMessage(data) {
    const { type, content } = data;

    if (type === 'typing') {
      // 新建一条空白 AI 消息，后续 chunk 追加进去
      const id = `ai_${Date.now()}`;
      this._streamingMsgId = id;
      this.setData({
        isTyping: true,
        messages: [...this.data.messages, { id, role: 'ai', content: '' }],
      });
      this._scrollToBottom();

    } else if (type === 'chunk') {
      // 找到当前流式消息，追加内容
      if (!this._streamingMsgId) return;
      const messages = this.data.messages.map((m) =>
        m.id === this._streamingMsgId
          ? { ...m, content: m.content + content }
          : m
      );
      this.setData({ messages });
      this._scrollToBottom();

    } else if (type === 'done') {
      this._streamingMsgId = null;
      this.setData({ isTyping: false });

    } else if (type === 'error') {
      this._streamingMsgId = null;
      this.setData({ isTyping: false });
      wx.showToast({ title: content || '出错了，请重试', icon: 'none' });
    }
  },

  // ─── 发送消息 ─────────────────────────────────────────────────

  onSend() {
    const text = this.data.inputText.trim();
    if (!text || !this.data.connected || this.data.isTyping) return;

    const msg = { id: `user_${Date.now()}`, role: 'user', content: text };
    this.setData({
      messages: [...this.data.messages, msg],
      inputText: '',
    });

    this._ws.send(text);
    this._scrollToBottom();
  },

  onInputChange(e) {
    this.setData({ inputText: e.detail.value });
  },

  // ─── 滚动到底 ─────────────────────────────────────────────────

  _scrollToBottom() {
    const msgs = this.data.messages;
    if (!msgs.length) return;
    this.setData({ scrollToId: 'msg-' + msgs[msgs.length - 1].id });
  },
});
