/**
 * AI Arena - API 调用封装
 */

const API = {
    async getConfig() {
        const res = await fetch('/api/config');
        return res.json();
    },

    async saveConfig(config) {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config),
        });
        return res.json();
    },

    async testConnection(model) {
        const res = await fetch('/api/config/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(model),
        });
        return res.json();
    },

    async getScenarios() {
        const res = await fetch('/api/scenarios');
        return res.json();
    },

    async startGame(data) {
        const res = await fetch('/api/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    },

    async stopGame() {
        const res = await fetch('/api/game/stop', { method: 'POST' });
        return res.json();
    },

    async resetGame() {
        const res = await fetch('/api/game/reset', { method: 'POST' });
        return res.json();
    },

    async getGameState() {
        const res = await fetch('/api/game/state');
        return res.json();
    },

    async pauseGame() {
        const res = await fetch('/api/game/pause', { method: 'POST' });
        return res.json();
    },

    async resumeGame() {
        const res = await fetch('/api/game/resume', { method: 'POST' });
        return res.json();
    },

    async getLeaderboard(scenario, limit) {
        const params = new URLSearchParams();
        if (scenario) params.set('scenario', scenario);
        if (limit) params.set('limit', String(limit));
        const res = await fetch('/api/leaderboard?' + params.toString());
        return res.json();
    },

    async getModelRating(modelName, scenario) {
        const params = new URLSearchParams();
        if (scenario) params.set('scenario', scenario);
        const res = await fetch('/api/rating/' + encodeURIComponent(modelName) + '?' + params.toString());
        return res.json();
    },

    async getChronicle() {
        const res = await fetch('/api/chronicle');
        return res.json();
    },

    async getReplay() {
        const res = await fetch('/api/replay');
        return res.json();
    },

    async getHallOfFame(scenario, limit) {
        const params = new URLSearchParams();
        if (scenario) params.set('scenario', scenario);
        if (limit) params.set('limit', String(limit));
        const res = await fetch('/api/hall-of-fame?' + params.toString());
        return res.json();
    },

    async getShareCard() {
        const res = await fetch('/api/share-card');
        return res.json();
    },
};
