/**
 * AI Arena - 工具函数
 */

const Helpers = {
    /**
     * 生成唯一 ID
     */
    generateId() {
        return 'id_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 5);
    },

    /**
     * 创建 DOM 元素
     */
    createElement(tag, attrs = {}, children = []) {
        const el = document.createElement(tag);
        for (const [key, value] of Object.entries(attrs)) {
            if (key === 'className') {
                el.className = value;
            } else if (key === 'textContent') {
                el.textContent = value;
            } else if (key === 'innerHTML') {
                el.innerHTML = value;
            } else if (key.startsWith('on')) {
                el.addEventListener(key.slice(2).toLowerCase(), value);
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(el.style, value);
            } else {
                el.setAttribute(key, value);
            }
        }
        for (const child of children) {
            if (typeof child === 'string') {
                el.appendChild(document.createTextNode(child));
            } else if (child) {
                el.appendChild(child);
            }
        }
        return el;
    },

    /**
     * 安全转义 HTML
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
};
