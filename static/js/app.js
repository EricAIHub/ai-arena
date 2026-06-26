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
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const page = btn.dataset.page;
                this.navigateTo(page);
            });
        });
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

        // 更新导航按钮状态
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.page === page);
        });

        const currentPageEl = document.getElementById(`page-${this.currentPage}`);
        const nextPageEl = document.getElementById(`page-${page}`);

        if (!currentPageEl || !nextPageEl) {
            // fallback：直接切换
            document.querySelectorAll('.page').forEach(p => {
                p.classList.toggle('active', p.id === `page-${page}`);
            });
            this.currentPage = page;
            return;
        }

        // 标记正在切换，防止重复触发
        if (this._navigating) return;
        this._navigating = true;

        // 先 exit 动画，再切换
        currentPageEl.classList.add('page-exit');

        const doSwitch = () => {
            // 清理旧页面
            currentPageEl.classList.remove('active', 'page-exit');
            currentPageEl.style.opacity = '';
            // 显示新页面
            nextPageEl.classList.add('active', 'page-enter');
            // 清理入场动画类
            setTimeout(() => {
                nextPageEl.classList.remove('page-enter');
                this._navigating = false;
            }, 350);
            this.currentPage = page;
        };

        // 监听动画结束，250ms 兜底确保切换
        let switched = false;
        const safeSwitch = () => {
            if (switched) return;
            switched = true;
            doSwitch();
        };
        currentPageEl.addEventListener('animationend', safeSwitch, { once: true });
        setTimeout(safeSwitch, 250); // 兜底
    },
};

// 启动应用
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
