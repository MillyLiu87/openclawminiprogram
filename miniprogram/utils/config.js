// utils/config.js — 小程序所有配置集中在这里
const Config = {
  // 后端服务地址（开发时填 VPS IP，上线后换域名）
  BACKEND_HTTP: 'http://91.99.106.216:8000',
  BACKEND_WS:   'ws://91.99.106.216:8000',

  // 开发模式：跳过 wx.login，直接用固定 openid 测试
  // 上线前改为 false
  DEV_MODE: true,
  DEV_OPENID: 'dev_test_user_001',

  // 接口路径
  API: {
    LOGIN:  '/auth/wx_login',
    CHAT:   '/chat',
    WS:     '/ws',      // WebSocket: /ws/{openid}
    STATUS: '/status',
  },

  // 重连配置
  WS_RECONNECT_DELAY: 3000,   // 断线后 3 秒重连
  WS_MAX_RETRIES: 5,
};

module.exports = Config;
