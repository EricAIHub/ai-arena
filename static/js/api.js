/**
 * AI Arena - API 调用封装
 */

const API = {
    /**
     * 获取配置
     */
    async getConfig() {
        const res = await fetch('/api/config');
        return res.json();
    },

    /**
     * 保存配置
     */
    async saveConfig(config) {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config),
        });
        return res.json();
    },

    /**
     * 测试模型连接
     */
    async testConnection(model) {
        const res = await fetch('/api/config/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(model),
        });
        return res.json();
    },

    /**
     * 获取场景列表
     */
    async getScenarios() {
        const res = await fetch('/api/scenarios');
        return res.json();
    },

    /**
     * 开始游戏
     */
    async startGame(data) {
        const res = await fetch('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    },

    /**
     * 停止游戏
     */
    async stopGame() {
        const res = await fetch('/api/game/stop', { method: 'POST' });
        return res.json();
    },

    /**
     * 重置游戏
     */
    async resetGame() {
        const res = await fetch('/api/game/reset', { method: 'POST' });
        return res.json();
    },

    /**
     * 获取游戏状态
     */
    async getGameState() {
        const res = await fetch('/api/game/state');
        return res.json();
    },

    /**
     * 暂停游戏
     */
    async pauseGame() {
        const res = await fetch('/api/game/pause', { method: 'POST' });
        return res.json();
    },

    /**
     * 继续游戏
     */
    async resumeGame() {
        const res = await fetch('/api/game/resume', { method: 'POST' });
        return res.json();
    },
};
