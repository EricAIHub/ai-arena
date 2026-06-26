/**
 * AI Arena — 主题系统（模式 + 配色 两层架构）
 */

const ThemeManager = {
    mode: 'dark',        // 'dark' | 'light'
    accent: 'clean',     // 'clean' | 'deluxe' | 'soft'
    uxMode: 'geek',      // 'geek' | 'spectator'

    accents: {
        clean:  { name: '纯净', emoji: '💎', primary: '#6366f1', primaryEnd: '#8b5cf6' },
        deluxe: { name: '豪华', emoji: '🔮', primary: '#8b5cf6', primaryEnd: '#a855f7' },
        soft:   { name: '柔和', emoji: '🍂', primary: '#d4956b', primaryEnd: '#e8b898' },
    },

    init() {
        // 兼容旧版 localStorage：如果有旧主题但没有新模式，做一次性迁移
        const legacyTheme = localStorage.getItem('ai-arena-theme');
        let savedMode = localStorage.getItem('ai-arena-mode');
        let savedAccent = localStorage.getItem('ai-arena-accent');

        if (!savedMode && legacyTheme) {
            // 旧主题迁移
            if (legacyTheme === 'light') {
                savedMode = 'light';
                savedAccent = 'clean';
            } else {
                savedMode = 'dark';
                savedAccent = legacyTheme;
            }
            localStorage.removeItem('ai-arena-theme');
        }

        this.apply(savedMode || 'dark', savedAccent || 'clean');
    },

    apply(mode, accent) {
        this.mode = mode;
        this.accent = accent;
        document.documentElement.setAttribute('data-mode', mode);
        document.documentElement.setAttribute('data-accent', accent);
        // 清理旧属性
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('ai-arena-mode', mode);
        localStorage.setItem('ai-arena-accent', accent);
        this.syncTitlebar();
        document.dispatchEvent(new CustomEvent('theme-changed', { detail: { mode, accent } }));
    },

    setMode(mode) {
        this.apply(mode, this.accent);
    },

    setAccent(accent) {
        this.apply(this.mode, accent);
    },

    /** 同步 Electron 标题栏 overlay 颜色 */
    syncTitlebar() {
        if (window.electronAPI && window.electronAPI.setTitleBarOverlay) {
            const isLight = this.mode === 'light';
            window.electronAPI.setTitleBarOverlay({
                color: isLight ? '#f5f5f7' : '#09090b',
                symbolColor: isLight ? '#1d1d1f' : '#ffffff',
            });
        }
    },

    setUxMode(mode) {
        this.uxMode = mode;
        document.documentElement.setAttribute('data-ux', mode);
        localStorage.setItem('ai-arena-ux', mode);
        document.dispatchEvent(new CustomEvent('ux-changed', { detail: { mode } }));
    },

    getTheme() {
        return {
            mode: this.mode,
            accent: this.accent,
            uxMode: this.uxMode,
            ...this.accents[this.accent],
        };
    },
};
