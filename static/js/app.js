/**
 * AI Arena - 主应用
 */

const App = {
    currentPage: 'config',

    async init() {
        console.log('🏟️ AI Arena 启动中...');

        // 初始化主题
        ThemeManager.init();

        // 连接 WebSocket
        gameWS.connect();

        // 初始化各组件
        await ConfigPanel.init();
        await ScenarioSelect.init();
        Arena.init();

        // 绑定导航
        this.bindNavigation();

        // 初始化设置页面
        this.initSettings();

        // 新手引导
        this.initOnboarding();

        console.log('✅ AI Arena 就绪');
    },

    initOnboarding() {
        const seen = localStorage.getItem('ai-arena-onboarding-seen');
        const card = document.getElementById('onboarding-card');
        if (!seen && card) {
            card.style.display = 'block';
        }
        const closeBtn = document.getElementById('btn-close-onboarding');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                card.style.display = 'none';
                localStorage.setItem('ai-arena-onboarding-seen', '1');
            });
        }
    },

    bindNavigation() {
        // 事件委托：绑定到 navbar-menu 容器，避免元素替换导致失效
        const menu = document.querySelector('.navbar-menu');
        if (menu) {
            menu.addEventListener('click', (e) => {
                const btn = e.target.closest('.nav-btn');
                if (btn && btn.dataset.page) {
                    this.navigateTo(btn.dataset.page);
                }
            });
        }
    },

    initSettings() {
        // UX 模式切换
        const uxToggle = document.getElementById('ux-mode-toggle');
        if (uxToggle) {
            uxToggle.querySelectorAll('.ux-mode-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    ThemeManager.setUxMode(btn.dataset.ux);
                });
            });
            document.addEventListener('ux-changed', () => {
                uxToggle.querySelectorAll('.ux-mode-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.ux === ThemeManager.uxMode);
                });
            });
            // 初始化
            const savedUx = localStorage.getItem('ai-arena-ux') || 'geek';
            ThemeManager.setUxMode(savedUx);
        }

        // 明暗模式切换
        const modeToggle = document.getElementById('mode-toggle');
        if (modeToggle) {
            modeToggle.querySelectorAll('.mode-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    ThemeManager.setMode(btn.dataset.mode);
                });
            });
            // 更新选中状态
            document.addEventListener('theme-changed', () => {
                modeToggle.querySelectorAll('.mode-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.mode === ThemeManager.mode);
                });
            });
            // 初始化
            modeToggle.querySelector(`[data-mode="${ThemeManager.mode}"]`)?.classList.add('active');
        }

        // 音效开关
        const soundToggle = document.getElementById('sound-toggle');
        if (soundToggle && typeof SoundFX !== 'undefined') {
            const savedSound = localStorage.getItem('ai-arena-sound');
            if (savedSound !== null) {
                SoundFX.enabled = savedSound === 'true';
                soundToggle.checked = SoundFX.enabled;
            }
            soundToggle.addEventListener('change', () => {
                SoundFX.enabled = soundToggle.checked;
                localStorage.setItem('ai-arena-sound', String(SoundFX.enabled));
                if (SoundFX.enabled) SoundFX.notify();
            });
        }

        // 配色方案选择
        const accentPicker = document.getElementById('accent-picker');
        if (accentPicker) {
            accentPicker.querySelectorAll('.accent-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    ThemeManager.setAccent(btn.dataset.accent);
                });
            });
            // 更新选中状态
            document.addEventListener('theme-changed', () => {
                accentPicker.querySelectorAll('.accent-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.accent === ThemeManager.accent);
                });
            });
            // 初始化
            accentPicker.querySelector(`[data-accent="${ThemeManager.accent}"]`)?.classList.add('active');
        }
    },

    navigateTo(page) {
        if (page === this.currentPage) return;
        if (this._navigating) return;
        this._navigating = true;

        // 更新导航按钮状态
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.page === page);
        });

        const currentPageEl = document.getElementById(`page-${this.currentPage}`);
        const nextPageEl = document.getElementById(`page-${page}`);

        if (!currentPageEl || !nextPageEl) {
            document.querySelectorAll('.page').forEach(p => {
                p.classList.toggle('active', p.id === `page-${page}`);
            });
            this.currentPage = page;
            this._navigating = false;
            return;
        }

        // 简单可靠方案：先隐藏旧页面，再显示新页面
        currentPageEl.classList.remove('active');
        currentPageEl.style.display = 'none';
        currentPageEl.style.opacity = '';
        currentPageEl.style.transform = '';

        nextPageEl.classList.add('active');
        nextPageEl.style.display = 'block';
        nextPageEl.style.opacity = '0';
        nextPageEl.style.transform = 'translateY(12px)';

        // 强制回流后播放入场动画
        void nextPageEl.offsetWidth;
        nextPageEl.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
        nextPageEl.style.opacity = '1';
        nextPageEl.style.transform = 'translateY(0)';

        setTimeout(() => {
            nextPageEl.style.transition = '';
            nextPageEl.style.transform = '';
            this._navigating = false;
        }, 280);

        this.currentPage = page;
    },
};

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
