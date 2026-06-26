/**
 * AI Arena - 程序化音效系统
 * 使用 Web Audio API 生成音效，无需外部音频文件
 */
const SoundFX = {
    ctx: null,
    enabled: true,
    volume: 0.3,

    init() {
        // 延迟初始化（需要用户交互后才能创建 AudioContext）
        document.addEventListener('click', () => {
            if (!this.ctx) {
                this.ctx = new (window.AudioContext || window.webkitAudioContext)();
            }
        }, { once: true });
    },

    _ensureCtx() {
        if (!this.ctx) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
        return this.ctx;
    },

    /** 播放音调 */
    _playTone(freq, duration, type = 'sine', fadeOut = true) {
        if (!this.enabled) return;
        const ctx = this._ensureCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type;
        osc.frequency.value = freq;
        gain.gain.value = this.volume;
        if (fadeOut) {
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
        }
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + duration);
    },

    /** 播放噪声 */
    _playNoise(duration, filterFreq = 1000) {
        if (!this.enabled) return;
        const ctx = this._ensureCtx();
        const bufferSize = ctx.sampleRate * duration;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }
        const source = ctx.createBufferSource();
        source.buffer = buffer;
        const filter = ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.value = filterFreq;
        const gain = ctx.createGain();
        gain.gain.value = this.volume * 0.3;
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
        source.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);
        source.start();
    },

    // ===== 游戏音效 =====

    /** 夜幕降临 — 低沉的嗡鸣 */
    nightFall() {
        this._playTone(80, 2, 'sine');
        setTimeout(() => this._playTone(60, 1.5, 'sine'), 300);
        this._playNoise(1.5, 200);
    },

    /** 天亮 — 上升音调 */
    dayBreak() {
        this._playTone(200, 0.3, 'sine');
        setTimeout(() => this._playTone(300, 0.3, 'sine'), 150);
        setTimeout(() => this._playTone(400, 0.5, 'sine'), 300);
    },

    /** 发言 — 短促提示音 */
    speech() {
        this._playTone(440, 0.1, 'sine');
    },

    /** 投票 — 紧张音效 */
    vote() {
        this._playTone(220, 0.2, 'square');
        setTimeout(() => this._playTone(330, 0.2, 'square'), 200);
    },

    /** 淘汰 — 下降音调 + 噪声 */
    death() {
        this._playTone(400, 0.3, 'sawtooth');
        setTimeout(() => this._playTone(200, 0.5, 'sawtooth'), 200);
        setTimeout(() => this._playNoise(0.8, 500), 400);
    },

    /** 游戏结束 — 胜利音效 */
    victory() {
        const notes = [523, 659, 784, 1047]; // C5 E5 G5 C6
        notes.forEach((freq, i) => {
            setTimeout(() => this._playTone(freq, 0.4, 'sine'), i * 200);
        });
    },

    /** 按钮点击 */
    click() {
        this._playTone(800, 0.05, 'sine');
    },

    /** 通知 */
    notify() {
        this._playTone(600, 0.15, 'sine');
        setTimeout(() => this._playTone(800, 0.15, 'sine'), 100);
    },

    /** 暂停 */
    pause() {
        this._playTone(300, 0.2, 'triangle');
    },

    /** 继续 */
    resume() {
        this._playTone(500, 0.2, 'triangle');
        setTimeout(() => this._playTone(700, 0.2, 'triangle'), 150);
    },

    /** 预言家查验 — 神秘音效 */
    seerCheck() {
        this._playTone(440, 0.3, 'sine');
        setTimeout(() => this._playTone(554, 0.3, 'sine'), 200);
        setTimeout(() => this._playTone(659, 0.5, 'sine'), 400);
    },

    /** 狼人嚎叫 */
    wolfHowl() {
        const ctx = this._ensureCtx();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(200, ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(400, ctx.currentTime + 0.5);
        osc.frequency.linearRampToValueAtTime(150, ctx.currentTime + 1.5);
        gain.gain.value = this.volume * 0.2;
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 2);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 2);
    },

    /** 切换开关 */
    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    },
};

// 初始化
document.addEventListener('DOMContentLoaded', () => SoundFX.init());
