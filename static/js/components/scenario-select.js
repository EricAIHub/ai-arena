/**
 * AI Arena - 场景选择组件
 */

const ScenarioSelect = {
    scenarios: [],
    selectedScenario: null,
    players: [],

    async init() {
        // 显示骨架屏
        const grid = document.getElementById('scenario-grid');
        if (grid) Skeleton.inject(grid, 'scenarios', 5);

        await this.loadScenarios();
        this.render();
        this.bindEvents();
    },

    async loadScenarios() {
        try {
            const data = await API.getScenarios();
            this.scenarios = data.scenarios || [];
        } catch (e) {
            console.error('加载场景失败:', e);
            this.scenarios = [];
        }
    },

    render() {
        const grid = document.getElementById('scenario-grid');
        grid.innerHTML = '';

        if (this.scenarios.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <span class="empty-state-emoji">🎯</span>
                    <div class="empty-state-title">暂无可用场景</div>
                    <div class="empty-state-desc">请检查 data/scenarios 目录下是否有场景配置文件</div>
                </div>
            `;
            return;
        }

        this.scenarios.forEach(scenario => {
            grid.appendChild(this.createScenarioCard(scenario));
        });
    },

    createScenarioCard(scenario) {
        const card = Helpers.createElement('div', {
            className: 'card scenario-card',
            'data-scenario': scenario.id,
        });

        card.innerHTML = `
            <div class="scenario-emoji">${scenario.emoji}</div>
            <div class="scenario-name">${Helpers.escapeHtml(scenario.name)}</div>
            <div class="scenario-desc">${Helpers.escapeHtml(scenario.description)}</div>
            <div class="scenario-meta">
                <span class="badge badge-primary">${scenario.min_players}-${scenario.max_players} 人</span>
            </div>
        `;

        card.addEventListener('click', () => this.selectScenario(scenario));

        return card;
    },

    selectScenario(scenario) {
        this.selectedScenario = scenario;
        this.showPlayerSetup(scenario);
    },

    showPlayerSetup(scenario) {
        // 隐藏场景网格，显示玩家配置
        const grid = document.getElementById('scenario-grid');
        grid.style.display = 'none';

        // 创建玩家配置面板
        let setupPanel = document.getElementById('player-setup');
        if (!setupPanel) {
            setupPanel = document.createElement('div');
            setupPanel.id = 'player-setup';
            setupPanel.className = 'player-setup';
            grid.parentNode.appendChild(setupPanel);
        }

        const config = ConfigPanel.models;
        const charDefaults = CharacterModels.getDefaultsForScenario(scenario.id, scenario.min_players);
        const defaultPlayers = [];
        for (let i = 0; i < scenario.min_players; i++) {
            const model = config[i % config.length] || { name: '未配置', emoji: '🤖' };
            const charId = charDefaults[i] || 'robot';
            const charModel = CharacterModels.get(charId);
            defaultPlayers.push({
                id: Helpers.generateId(),
                name: `${charModel.name} ${i + 1}`,
                model_name: model.name,
                emoji: charModel.emoji,
                color: charModel.color,
                character: charId,
                personality: '',
            });
        }
        this.players = defaultPlayers;

        setupPanel.innerHTML = `
            <div class="card" style="max-width: 800px; margin: 0 auto;">
                <div class="card-header">
                    <span style="font-size: 2rem;">${scenario.emoji}</span>
                    <div>
                        <div class="card-title">${Helpers.escapeHtml(scenario.name)} — 玩家配置</div>
                        <div style="font-size: var(--text-sm); color: var(--color-text-secondary);">
                            配置 ${scenario.min_players}-${scenario.max_players} 名 AI 选手
                        </div>
                    </div>
                </div>
                <div id="player-list" class="player-list" style="display: flex; flex-direction: column; gap: var(--space-3); margin-bottom: var(--space-4);">
                </div>
                <div style="display: flex; gap: var(--space-3); justify-content: flex-end;">
                    <button class="btn btn-secondary" id="btn-back-scenarios">← 返回</button>
                    <button class="btn btn-primary" id="btn-start-game">⚔️ 开始对战</button>
                </div>
            </div>
        `;

        this.renderPlayerList();

        // 绑定事件
        document.getElementById('btn-back-scenarios').addEventListener('click', () => {
            setupPanel.remove();
            grid.style.display = '';
        });

        document.getElementById('btn-start-game').addEventListener('click', () => {
            this.startGame();
        });
    },

    renderPlayerList() {
        const container = document.getElementById('player-list');
        if (!container) return;
        container.innerHTML = '';

        this.players.forEach((player, index) => {
            const row = Helpers.createElement('div', {
                className: 'player-row',
                style: 'display: flex; gap: var(--space-2); align-items: center;',
            });

            const charOptions = CharacterModels.getOptionsHTML(player.character || 'robot');

            row.innerHTML = `
                <select class="input character-select" data-player-index="${index}" data-player-field="character" style="flex: 1.2;">
                    ${charOptions}
                </select>
                <input class="input" type="text" value="${Helpers.escapeHtml(player.name)}" 
                       data-player-index="${index}" data-player-field="name" 
                       placeholder="玩家名" style="flex: 2;">
                <input class="input" type="text" value="${Helpers.escapeHtml(player.personality)}" 
                       data-player-index="${index}" data-player-field="personality" 
                       placeholder="如：冷静理性、善于分析、说话毒舌..." style="flex: 3;">
            `;

            container.appendChild(row);
        });

        // 输入变化
        container.addEventListener('change', (e) => {
            if (e.target.dataset.playerIndex !== undefined) {
                const index = parseInt(e.target.dataset.playerIndex);
                const field = e.target.dataset.playerField;
                this.players[index][field] = e.target.value;

                // 角色选择联动：自动更新 emoji 和颜色
                if (field === 'character') {
                    const charModel = CharacterModels.get(e.target.value);
                    this.players[index].emoji = charModel.emoji;
                    this.players[index].color = charModel.color;
                    // 更新名字（如果名字还是默认的）
                    const nameInput = container.querySelector(`[data-player-index="${index}"][data-player-field="name"]`);
                    if (nameInput) {
                        const oldName = nameInput.value;
                        // 如果名字以旧角色名开头，替换为新角色名
                        const allChars = CharacterModels.getAll();
                        const matchedOld = allChars.find(c => oldName.startsWith(c.name));
                        if (matchedOld) {
                            const newName = oldName.replace(matchedOld.name, charModel.name);
                            nameInput.value = newName;
                            this.players[index].name = newName;
                        }
                    }
                }
            }
        });
    },

    async startGame() {
        if (!this.selectedScenario) return;

        const startBtn = document.getElementById('btn-start-game');
        startBtn.disabled = true;
        startBtn.textContent = '⏳ 启动中...';

        try {
            const result = await API.startGame({
                scenario: this.selectedScenario.id,
                players: this.players,
                models: ConfigPanel.models,
            });

            if (result.error) {
                Toast.error(result.error);
                return;
            }

            // 切换到观战页面
            App.navigateTo('arena');
            Arena.onGameStart(this.selectedScenario, this.players);

        } catch (e) {
            console.error('启动游戏失败:', e);
            Toast.error('启动游戏失败: ' + e.message);
        } finally {
            startBtn.disabled = false;
            startBtn.textContent = '⚔️ 开始对战';
        }
    },

    bindEvents() {
        // 其他事件绑定
    },
};
