/**
 * AI Arena - WebSocket 客户端
 */

class GameWebSocket {
    constructor() {
        this.ws = null;
        this.callbacks = [];
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
        this.reconnectAttempts = 0;
        this.heartbeatInterval = null;
    }

    /** 更新连接状态 UI */
    _updateStatus(status) {
        const el = document.getElementById('ws-status');
        const bar = document.getElementById('ws-reconnect-bar');
        if (el) {
            el.dataset.status = status;
            const textEl = el.querySelector('.ws-status-text');
            if (textEl) {
                const labels = { connected: '已连接', connecting: '连接中...', disconnected: '已断开' };
                textEl.textContent = labels[status] || status;
            }
        }
        if (bar) {
            bar.classList.toggle('visible', status === 'disconnected');
        }
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/game`;

        this._updateStatus('connecting');
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            console.log('[WS] Connected');
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            this._startHeartbeat();
            this._updateStatus('connected');
        };

        this.ws.onmessage = (event) => {
            if (event.data === 'pong') return;
            try {
                const data = JSON.parse(event.data);
                this._notify(data);
            } catch (e) {
                console.error('[WS] Parse error:', e);
            }
        };

        this.ws.onclose = () => {
            console.log('[WS] Disconnected');
            this._stopHeartbeat();
            this._updateStatus('disconnected');
            this._reconnect();
        };

        this.ws.onerror = (error) => {
            console.error('[WS] Error:', error);
        };
    }

    _startHeartbeat() {
        this._stopHeartbeat();
        this.heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send('ping');
            }
        }, 30000);
    }

    _stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    _reconnect() {
        this.reconnectAttempts++;
        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
            this.maxReconnectDelay
        );
        const jitter = delay * (0.5 + Math.random() * 0.5);
        console.log(`[WS] Reconnecting in ${Math.round(jitter / 1000)}s...`);
        setTimeout(() => this.connect(), jitter);
    }

    onEvent(callback) {
        this.callbacks.push(callback);
    }

    offEvent(callback) {
        this.callbacks = this.callbacks.filter(cb => cb !== callback);
    }

    _notify(data) {
        for (const cb of this.callbacks) {
            try {
                cb(data);
            } catch (e) {
                console.error('[WS] Callback error:', e);
            }
        }
    }

    disconnect() {
        this._stopHeartbeat();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// 全局 WebSocket 实例
const gameWS = new GameWebSocket();
