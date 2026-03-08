// utils/ws.js — WebSocket 封装，含自动重连
const Config = require('./config');

class WsClient {
  constructor({ openid, onMessage, onConnect, onDisconnect }) {
    this.openid = openid;
    this.onMessage = onMessage;
    this.onConnect = onConnect;
    this.onDisconnect = onDisconnect;
    this._socket = null;
    this._retries = 0;
    this._closed = false;
  }

  connect() {
    this._closed = false;
    const url = `${Config.BACKEND_WS}${Config.API.WS}/${this.openid}`;
    console.log('[WS] Connecting:', url);

    this._socket = wx.connectSocket({ url, fail: (err) => console.error('[WS] connect fail', err) });

    this._socket.onOpen(() => {
      console.log('[WS] Connected');
      this._retries = 0;
      this.onConnect && this.onConnect();
    });

    this._socket.onMessage((res) => {
      try {
        const data = JSON.parse(res.data);
        this.onMessage && this.onMessage(data);
      } catch (e) {
        console.error('[WS] parse error', e);
      }
    });

    this._socket.onClose(() => {
      console.log('[WS] Disconnected');
      this.onDisconnect && this.onDisconnect();
      if (!this._closed) this._reconnect();
    });

    this._socket.onError((err) => {
      console.error('[WS] Error', err);
    });
  }

  send(message) {
    if (!this._socket) return;
    this._socket.send({ data: JSON.stringify({ message }) });
  }

  close() {
    this._closed = true;
    this._socket && this._socket.close();
  }

  _reconnect() {
    if (this._retries >= Config.WS_MAX_RETRIES) {
      console.warn('[WS] Max retries reached');
      return;
    }
    this._retries++;
    console.log(`[WS] Reconnecting in ${Config.WS_RECONNECT_DELAY}ms (attempt ${this._retries})`);
    setTimeout(() => this.connect(), Config.WS_RECONNECT_DELAY);
  }
}

module.exports = WsClient;
