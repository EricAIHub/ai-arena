/**
 * AI Arena - 配置面板组件
 */

const ConfigPanel = {
    models: [],

    // 预设模板
    presets: {
        deepseek: {
            name: 'DeepSeek',
            emoji: '🧊',
            base_url: 'https://api.deepseek.com/v1',
            model_name: 'deepseek-chat',
        },
        qwen: {
            name: '通义千问',
            emoji: '🌟',
            base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            model_name: 'qwen-plus',
        },
        kimi: {
            name: 'Kimi',
            emoji: '🌙',
            base_url: 'https://api.moonshot.cn/v1',
            model_name: 'moonshot-v1-8k',
        },
        openai: {
            name: 'OpenAI',
            emoji: '🤖',
            base_url: 'https://api.openai.com/v1',
            model_name: 'gpt-4o',
        },
        custom: {
            name: '自定义',
            emoji: '🔧',
            base_url: '',
            model_name: '',
        },
    },

    async init() {
        // 显示骨架屏
        const container = document.getElementById('model-list');
        if (container) Skeleton.inject(container, 'models', 3);

        await this.loadModels();
        this.render();
        this.bindEvents();
    },

    async loadModels() {
        try {
            const data = await API.getConfig();
            this.models = data.models || [];
        } catch (e) {
            console.error('加载配置失败:', e);
            this.models = [];
        }
    },

    render() {
        const container = document.getElementById('model-list');
        container.innerHTML = '';

        if (this.models.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span class="empty-state-emoji">🤖</span>
                    <div class="empty-state-title">还没有配置任何 AI 模型</div>
                    <div class="empty-state-desc">点击下方按钮添加你的第一个 AI 模型，开始精彩的对战之旅</div>
                </div>
            `;
            return;
        }

        this.models.forEach((model, index) => {
            container.appendChild(this.createModelCard(model, index));
        });
    },

    createModelCard(model, index) {
        const card = Helpers.createElement('div', { className: 'card model-card' });

        card.innerHTML = `
            <div class="model-card-header">
                <div class="model-name">
                    <span class="model-emoji">${model.emoji || '🤖'}</span>
                    <span>${Helpers.escapeHtml(model.name || '未命名模型')}</span>
                </div>
                <div class="model-card-actions">
                    <button class="btn btn-sm btn-secondary" data-action="test" data-index="${index}">🔌 测试</button>
                    <button class="btn btn-sm btn-danger" data-action="delete" data-index="${index}">🗑️ 删除</button>
                </div>
            </div>
            <div class="model-card-fields">
                <div class="input-group">
                    <label class="input-label">Base URL</label>
                    <input class="input" type="text" value="${Helpers.escapeHtml(model.base_url || '')}" 
                           data-field="base_url" data-index="${index}" placeholder="https://api.example.com/v1">
                </div>
                <div class="input-group">
                    <label class="input-label">API Key</label>
                    <div style="display: flex; gap: var(--space-2);">
                        <input class="input" type="password" value="${Helpers.escapeHtml(model.api_key || '')}" 
                               data-field="api_key" data-index="${index}" placeholder="sk-... 或其他服务商的 Key" style="flex: 1;">
                        <button class="btn btn-sm btn-secondary" data-action="toggle-key" data-index="${index}" title="显示/隐藏" style="min-width: 36px;">👁️</button>
                    </div>
                </div>
                <div class="input-group">
                    <label class="input-label">模型名称</label>
                    <input class="input" type="text" value="${Helpers.escapeHtml(model.model_name || '')}" 
                           data-field="model_name" data-index="${index}" placeholder="deepseek-chat">
                </div>
                <div class="input-group">
                    <label class="input-label">名称 + Emoji</label>
                    <div style="display: flex; gap: var(--space-2);">
                        <input class="input" type="text" value="${Helpers.escapeHtml(model.name || '')}" 
                               data-field="name" data-index="${index}" placeholder="DeepSeek" style="flex: 2;">
                        <input class="input" type="text" value="${Helpers.escapeHtml(model.emoji || '')}" 
                               data-field="emoji" data-index="${index}" placeholder="🧊" style="flex: 1;">
                    </div>
                </div>
            </div>
        `;

        return card;
    },

    bindEvents() {
        // 添加模型按钮
        document.getElementById('btn-add-model').addEventListener('click', () => {
            this.showPresetMenu();
        });

        // 事件委托
        document.getElementById('model-list').addEventListener('click', async (e) => {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;

            const action = btn.dataset.action;
            const index = parseInt(btn.dataset.index);

            if (action === 'delete') {
                this.models.splice(index, 1);
                this.render();
                await this.saveModels();
                Toast.success('模型已删除');
            } else if (action === 'toggle-key') {
                const card = document.querySelectorAll('.model-card')[index];
                if (card) {
                    const input = card.querySelector('[data-field="api_key"]');
                    if (input) {
                        input.type = input.type === 'password' ? 'text' : 'password';
                    }
                }
            } else if (action === 'test') {
                btn.disabled = true;
                btn.textContent = '⏳ 测试中...';
                try {
                    const model = this.collectModelData(index);
                    const result = await API.testConnection(model);
                    if (result.success) {
                        btn.textContent = '✅ 成功';
                        btn.style.color = 'var(--color-success)';
                    } else {
                        btn.textContent = '❌ 失败';
                        btn.style.color = 'var(--color-danger)';
                    }
                } catch (e) {
                    btn.textContent = '❌ 错误';
                    btn.style.color = 'var(--color-danger)';
                }
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = '🔌 测试';
                    btn.style.color = '';
                }, 3000);
            }
        });

        // 输入变化自动保存
        document.getElementById('model-list').addEventListener('change', async (e) => {
            const input = e.target;
            if (input.dataset.field && input.dataset.index !== undefined) {
                const index = parseInt(input.dataset.index);
                const field = input.dataset.field;
                this.models[index][field] = input.value;
                await this.saveModels();
            }
        });
    },

    collectModelData(index) {
        const card = document.querySelectorAll('.model-card')[index];
        if (!card) return this.models[index];

        const data = { ...this.models[index] };
        card.querySelectorAll('[data-field]').forEach(input => {
            data[input.dataset.field] = input.value;
        });
        return data;
    },

    async saveModels() {
        try {
            await API.saveConfig({ models: this.models });
        } catch (e) {
            console.error('保存配置失败:', e);
        }
    },

    showPresetMenu() {
        // 移除已有菜单
        const existing = document.getElementById('preset-menu');
        if (existing) { existing.remove(); return; }

        const menu = Helpers.createElement('div', { id: 'preset-menu', className: 'card' });
        menu.style.cssText = 'position: absolute; z-index: 100; padding: var(--space-2); min-width: 200px;';

        Object.entries(this.presets).forEach(([key, preset]) => {
            const btn = Helpers.createElement('button', { className: 'btn btn-secondary' });
            btn.style.cssText = 'width: 100%; text-align: left; margin-bottom: 2px; justify-content: flex-start;';
            btn.textContent = `${preset.emoji} ${preset.name}`;
            btn.addEventListener('click', () => {
                this.models.push({
                    name: preset.name,
                    emoji: preset.emoji,
                    base_url: preset.base_url,
                    model_name: preset.model_name,
                    api_key: '',
                    color: '#666666',
                });
                this.render();
                menu.remove();
                Toast.success(`已添加 ${preset.name}`);
            });
            menu.appendChild(btn);
        });

        // 定位到添加按钮旁边
        const addBtn = document.getElementById('btn-add-model');
        addBtn.style.position = 'relative';
        addBtn.parentNode.insertBefore(menu, addBtn.nextSibling);

        // 点击外部关闭
        const close = (e) => {
            if (!menu.contains(e.target) && e.target !== addBtn) {
                menu.remove();
                document.removeEventListener('click', close);
            }
        };
        setTimeout(() => document.addEventListener('click', close), 0);
    },
};
