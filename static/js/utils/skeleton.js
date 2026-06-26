/**
 * AI Arena - 骨架屏组件
 * 使用 shimmer 动画提供加载占位效果
 * 支持模型列表（3个）和场景列表（5个）骨架卡片
 */

const Skeleton = {
    /**
     * 创建模型列表骨架屏
     * @param {number} count - 骨架卡片数量，默认 3
     * @returns {DocumentFragment}
     */
    modelCards(count = 3) {
        const fragment = document.createDocumentFragment();
        for (let i = 0; i < count; i++) {
            const card = document.createElement('div');
            card.className = 'card skeleton-card';
            card.style.cssText = `
                padding-left: calc(var(--space-5, 1.25rem) + 4px);
                border-left: 4px solid rgba(255, 255, 255, 0.06);
                animation-delay: ${i * 80}ms;
            `;
            card.innerHTML = `
                <div class="skeleton-card-header" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div class="skeleton-block" style="width: 28px; height: 28px; border-radius: 6px;"></div>
                        <div class="skeleton-block" style="width: 100px; height: 16px; border-radius: 4px;"></div>
                    </div>
                    <div style="display: flex; gap: 6px;">
                        <div class="skeleton-block" style="width: 56px; height: 28px; border-radius: 6px;"></div>
                        <div class="skeleton-block" style="width: 56px; height: 28px; border-radius: 6px;"></div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
                    <div>
                        <div class="skeleton-block" style="width: 50px; height: 10px; border-radius: 3px; margin-bottom: 6px;"></div>
                        <div class="skeleton-block" style="width: 100%; height: 36px; border-radius: 8px;"></div>
                    </div>
                    <div>
                        <div class="skeleton-block" style="width: 40px; height: 10px; border-radius: 3px; margin-bottom: 6px;"></div>
                        <div class="skeleton-block" style="width: 100%; height: 36px; border-radius: 8px;"></div>
                    </div>
                    <div>
                        <div class="skeleton-block" style="width: 60px; height: 10px; border-radius: 3px; margin-bottom: 6px;"></div>
                        <div class="skeleton-block" style="width: 100%; height: 36px; border-radius: 8px;"></div>
                    </div>
                </div>
            `;
            fragment.appendChild(card);
        }
        return fragment;
    },

    /**
     * 创建场景列表骨架屏
     * @param {number} count - 骨架卡片数量，默认 5
     * @returns {DocumentFragment}
     */
    scenarioCards(count = 5) {
        const fragment = document.createDocumentFragment();
        for (let i = 0; i < count; i++) {
            const card = document.createElement('div');
            card.className = 'card skeleton-card';
            card.style.cssText = `
                border-radius: 16px;
                padding: 20px;
                animation-delay: ${i * 80}ms;
            `;
            card.innerHTML = `
                <div class="skeleton-block" style="width: 48px; height: 48px; border-radius: 10px; margin-bottom: 16px;"></div>
                <div class="skeleton-block" style="width: 70%; height: 18px; border-radius: 4px; margin-bottom: 10px;"></div>
                <div class="skeleton-block" style="width: 100%; height: 12px; border-radius: 3px; margin-bottom: 5px;"></div>
                <div class="skeleton-block" style="width: 85%; height: 12px; border-radius: 3px; margin-bottom: 16px;"></div>
                <div class="skeleton-block" style="width: 60px; height: 20px; border-radius: 9999px;"></div>
            `;
            fragment.appendChild(card);
        }
        return fragment;
    },

    /**
     * 向容器注入骨架屏
     * @param {HTMLElement} container - 目标容器
     * @param {'models'|'scenarios'} type - 类型
     * @param {number} count - 数量
     */
    inject(container, type, count) {
        if (!container) return;
        container.innerHTML = '';
        if (type === 'models') {
            container.appendChild(this.modelCards(count));
        } else if (type === 'scenarios') {
            container.appendChild(this.scenarioCards(count));
        }
    },
};

// 注入骨架屏样式
(function injectSkeletonStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .skeleton-card {
            pointer-events: none;
        }
        .skeleton-block {
            background: linear-gradient(
                90deg,
                rgba(255, 255, 255, 0.03) 25%,
                rgba(255, 255, 255, 0.07) 50%,
                rgba(255, 255, 255, 0.03) 75%
            );
            background-size: 200% 100%;
            animation: shimmer 1.5s ease-in-out infinite;
        }
    `;
    document.head.appendChild(style);
})();
