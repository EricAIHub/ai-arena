/**
 * AI Arena - Toast 通知系统
 * 右上角弹出，支持 success/error/warning/info 四种类型
 * 玻璃拟态风格，自动消失（3秒），可手动关闭
 * 动画：slideInRight + fadeOut
 */

const Toast = {
    container: null,

    _ensureContainer() {
        if (this.container) return;
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.style.cssText = `
            position: fixed;
            top: calc(var(--navbar-height, 56px) + 12px);
            right: 16px;
            z-index: var(--z-toast, 2000);
            display: flex;
            flex-direction: column;
            gap: 8px;
            pointer-events: none;
            max-width: 380px;
        `;
        document.body.appendChild(this.container);
    },

    /**
     * 显示一条 toast
     * @param {string} message - 消息内容
     * @param {'success'|'error'|'warning'|'info'} type - 类型
     * @param {number} duration - 持续时间（ms），默认 3000
     */
    show(message, type = 'info', duration = 3000) {
        this._ensureContainer();

        const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
        const colors = {
            success: { border: 'rgba(34, 197, 94, 0.3)', glow: 'rgba(34, 197, 94, 0.12)', text: '#22c55e' },
            error:   { border: 'rgba(239, 68, 68, 0.3)', glow: 'rgba(239, 68, 68, 0.12)', text: '#ef4444' },
            warning: { border: 'rgba(234, 179, 8, 0.3)', glow: 'rgba(234, 179, 8, 0.12)', text: '#eab308' },
            info:    { border: 'rgba(99, 102, 241, 0.3)', glow: 'rgba(99, 102, 241, 0.12)', text: '#818cf8' },
        };
        const c = colors[type] || colors.info;

        const toast = document.createElement('div');
        toast.className = 'toast-item';
        toast.style.cssText = `
            pointer-events: auto;
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 12px 16px;
            background: linear-gradient(145deg, rgba(17, 17, 24, 0.92), rgba(25, 25, 32, 0.82));
            border: 1px solid ${c.border};
            border-radius: 12px;
            backdrop-filter: blur(20px) saturate(1.8);
            -webkit-backdrop-filter: blur(20px) saturate(1.8);
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.04),
                0 8px 30px rgba(0, 0, 0, 0.4),
                0 0 20px ${c.glow};
            animation: toastSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) both;
            cursor: pointer;
            max-width: 100%;
            word-break: break-word;
        `;

        toast.innerHTML = `
            <span style="font-size: 16px; flex-shrink: 0; line-height: 1.4;">${icons[type] || icons.info}</span>
            <span style="flex: 1; font-size: 13px; line-height: 1.5; color: var(--color-text, #f0f0f5);">${message}</span>
            <span style="flex-shrink: 0; opacity: 0.4; cursor: pointer; font-size: 14px; line-height: 1.4; transition: opacity 0.15s;" 
                  onmouseenter="this.style.opacity='1'" onmouseleave="this.style.opacity='0.4'">✕</span>
        `;

        // 关闭按钮
        const closeBtn = toast.querySelector('span:last-child');
        const dismiss = () => this._dismiss(toast);
        closeBtn.addEventListener('click', (e) => { e.stopPropagation(); dismiss(); });
        toast.addEventListener('click', dismiss);

        this.container.appendChild(toast);

        // 自动消失
        if (duration > 0) {
            setTimeout(dismiss, duration);
        }
    },

    _dismiss(toast) {
        if (toast._dismissing) return;
        toast._dismissing = true;
        toast.style.animation = 'toastFadeOut 0.25s ease forwards';
        setTimeout(() => toast.remove(), 250);
    },

    success(msg, duration) { this.show(msg, 'success', duration); },
    error(msg, duration)   { this.show(msg, 'error', duration); },
    warning(msg, duration) { this.show(msg, 'warning', duration); },
    info(msg, duration)    { this.show(msg, 'info', duration); },
};

// 注入 toast 动画 keyframes
(function injectToastStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes toastSlideIn {
            from {
                opacity: 0;
                transform: translateX(60px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateX(0) scale(1);
            }
        }
        @keyframes toastFadeOut {
            from {
                opacity: 1;
                transform: translateX(0) scale(1);
            }
            to {
                opacity: 0;
                transform: translateX(40px) scale(0.95);
            }
        }
    `;
    document.head.appendChild(style);
})();
