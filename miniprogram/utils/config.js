// utils/config.js — 小程序所有配置集中在这里
const Config = {
  // 后端服务地址（生产必须 https/wss + 域名，微信强制要求）
  BACKEND_HTTP: 'https://chat.clawhelp.net',
  BACKEND_WS:   'wss://chat.clawhelp.net',

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
