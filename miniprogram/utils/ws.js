// utils/ws.js — 优先 WebSocket，失败自动降级到 HTTP 轮询
const Config = require('./config');

class WsClient {
  constructor({ openid, onMessage, onConnect, onDisconnect }) {
    this.openid = openid;
    this.onMessage = onMessage;
    this.onConnect = onConnect;
    this.onDisconnect = onDisconnect;
    this._socket = null;
    this._mode = 'ws';       // 'ws' | 'http'
    this._retries = 0;
    this._closed = false;
  }

  connect() {
    this._closed = false;
    this._tryWebSocket();
  }

  // ─── WebSocket 模式 ────────────────────────────────────────────

  _tryWebSocket() {
    const url = `${Config.BACKEND_WS}${Config.API.WS}/${this.openid}`;
    console.log('[WS] Connecting:', url);

    this._socket = wx.connectSocket({
      url,
      fail: () => {
        console.log('[WS] Connect failed, falling back to HTTP polling');
        this._switchToHttp();
      }
    });

    // 3 秒没连上就切 HTTP
    const fallbackTimer = setTimeout(() => {
      if (this._mode === 'ws' && !this._wsOpen) {
        console.log('[WS] Timeout, switching to HTTP polling');
        this._switchToHttp();
      }
    }, 3000);

    this._socket.onOpen(() => {
      clearTimeout(fallbackTimer);
      this._wsOpen = true;
      this._mode = 'ws';
      console.log('[WS] Connected');
      this.onConnect && this.onConnect();
    });

    this._socket.onMessage((res) => {
      try {
        this.onMessage && this.onMessage(JSON.parse(res.data));
      } catch (e) { }
    });

    this._socket.onError(() => {
      clearTimeout(fallbackTimer);
      if (!this._wsOpen) this._switchToHttp();
    });

    this._socket.onClose(() => {
      this._wsOpen = false;
      if (!this._closed && this._mode === 'ws') {
        this.onDisconnect && this.onDisconnect();
        this._reconnect();
      }
    });
  }

  // ─── HTTP 轮询模式 ─────────────────────────────────────────────

  _switchToHttp() {
    this._mode = 'http';
    console.log('[HTTP] Switched to HTTP polling mode');
    this.onConnect && this.onConnect();   // 标记已连接
  }

  // 发消息：HTTP 模式直接 POST，WS 模式走 socket
  send(message) {
    if (this._mode === 'http') {
      this._httpSend(message);
    } else if (this._socket && this._wsOpen) {
      this._socket.send({ data: JSON.stringify({ message }) });
    }
  }

  _httpSend(message) {
    this.onMessage && this.onMessage({ type: 'typing' });

    wx.request({
      url: Config.BACKEND_HTTP + Config.API.CHAT,
      method: 'POST',
      data: { openid: this.openid, message },
      header: { 'Content-Type': 'application/json' },
      timeout: 60000,
      success: (res) => {
        if (res.data && res.data.reply) {
          // 模拟流式：一次性显示完整回复
          this.onMessage && this.onMessage({ type: 'chunk', content: res.data.reply });
          this.onMessage && this.onMessage({ type: 'done' });
        }
      },
      fail: (err) => {
        console.error('[HTTP] Request failed:', err);
        this.onMessage && this.onMessage({ type: 'error', content: '请求失败，请检查网络' });
      }
    });
  }

  // ─── 重连 ─────────────────────────────────────────────────────

  close() {
    this._closed = true;
    this._socket && this._socket.close();
  }

  _reconnect() {
    if (this._retries >= Config.WS_MAX_RETRIES) {
      console.log('[WS] Max retries, switching to HTTP');
      this._switchToHttp();
      return;
    }
    this._retries++;
    setTimeout(() => {
      if (!this._closed) this._tryWebSocket();
    }, Config.WS_RECONNECT_DELAY);
  }
}

module.exports = WsClient;
