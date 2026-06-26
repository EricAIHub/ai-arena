/**
 * AI Arena - 围桌对战观战面板组件
 * 沉浸式围桌布局：座位卡 + 气泡发言 + 阶段动效
 */

const Arena = {
    feedElement: null,
    playersElement: null,
    _players: [],
    _messageTimes: [],
    _isPaused: false,
    _thinkingIndicators: {},
    _playerSeats: {},
    _narratorTimeout: null,

    // 角色 emoji → CSS class 映射表
    _emojiCharMap: {
        '⚔️': 'char-warrior', '🗡️': 'char-assassin', '🧙': 'char-mage',
        '🔍': 'char-detective', '🥷': 'char-ninja', '🏴‍☠️': 'char-pirate',
        '🤖': 'char-robot', '👻': 'char-ghost', '🛡️': 'char-knight',
        '🪄': 'char-wizard', '💀': 'char-assassin', '🔮': 'char-mage',
        '🎯': 'char-detective', '⚔': 'char-warrior', '🛡': 'char-knight',
    },

    /**
     * 根据玩家数据推断角色 CSS class
     */
    _getCharClass(player) {
        if (!player) return '';
        // 1) 优先用 character_id
        if (player.character_id && CharacterModels?.models?.[player.character_id]) {
            return `char-${player.character_id}`;
        }
        // 2) 通过 emoji 反查
        if (player.emoji && this._emojiCharMap[player.emoji]) {
            return this._emojiCharMap[player.emoji];
        }
        // 3) 通过 color 近似匹配
        const colorMap = {
            '#ef4444': 'char-warrior', '#8b5cf6': 'char-mage', '#3b82f6': 'char-detective',
            '#4b5563': 'char-ninja', '#6b7280': 'char-ninja', '#f59e0b': 'char-pirate',
            '#06b6d4': 'char-robot', '#a78bfa': 'char-ghost', '#22c55e': 'char-knight',
            '#ec4899': 'char-wizard', '#dc2626': 'char-assassin',
        };
        if (player.color && colorMap[player.color.toLowerCase()]) {
            return colorMap[player.color.toLowerCase()];
        }
        return '';
    },

    init() {
        this.feedElement = document.getElementById('arena-feed');
        this.playersElement = document.getElementById('arena-players');

        // 绑定暂停按钮
        document.getElementById('btn-pause').addEventListener('click', async () => {
            if (this._isPaused) {
                await API.resumeGame();
                this._isPaused = false;
                document.getElementById('btn-pause').textContent = '⏸ 暂停';
                this.addSystemEvent('游戏已继续');
            } else {
                await API.pauseGame();
                this._isPaused = true;
                document.getElementById('btn-pause').textContent = '▶️ 继续';
                this.addSystemEvent('游戏已暂停');
            }
        });

        // 绑定停止按钮（带确认）
        document.getElementById('btn-stop').addEventListener('click', () => {
            this.showStopConfirm();
        });

        // 监听 WebSocket 事件
        gameWS.onEvent((event) => this.handleEvent(event));

        // 再来一局按钮
        this.setupPlayAgain();
    },

    setupPlayAgain() {
        this.playAgainBtn = document.createElement('button');
        this.playAgainBtn.className = 'btn btn-primary arena-play-again';
        this.playAgainBtn.textContent = '🔄 再来一局';
        this.playAgainBtn.addEventListener('click', () => {
            this.reset();
            App.navigateTo('scenarios');
        });
        // 插入到 speech-area 之后
        const speechArea = document.getElementById('arena-speech-area');
        if (speechArea) {
            speechArea.parentNode.insertBefore(this.playAgainBtn, speechArea.nextSibling);
        } else {
            this.feedElement.parentNode.appendChild(this.playAgainBtn);
        }
    },

    reset() {
        // 清空座位
        const seatsEl = document.getElementById('arena-seats');
        if (seatsEl) seatsEl.innerHTML = '';

        // 清空气泡区
        this.feedElement.innerHTML = '';

        // 清空底部状态栏
        this.playersElement.innerHTML = '';

        // 隐藏再来一局
        this.playAgainBtn.classList.remove('visible');

        // 重置中央区域
        const centerIcon = document.querySelector('.arena-center-icon');
        const centerText = document.querySelector('.arena-center-text');
        if (centerIcon) centerIcon.textContent = '🏟️';
        if (centerText) centerText.textContent = '等待开始...';

        // 重置头部
        document.getElementById('arena-emoji').textContent = '🏟️';
        document.getElementById('arena-scenario-name').textContent = '等待开始...';
        document.getElementById('arena-phase').textContent = '';
        document.getElementById('btn-stop').disabled = true;
        document.getElementById('btn-pause').disabled = true;

        // 重置内部状态
        this._players = [];
        this._messageTimes = [];
        this._isPaused = false;
        this._thinkingIndicators = {};
        this._playerSeats = {};
    },

    onGameStart(scenario) {
        // 重置暂停状态
        this._isPaused = false;
        document.getElementById('btn-pause').textContent = '⏸ 暂停';
        document.getElementById('btn-pause').disabled = false;

        // 清空发言区
        this.feedElement.innerHTML = '';
        this._messageTimes = [];
        this._thinkingIndicators = {};
        this._playerSeats = {};

        // 更新头部
        document.getElementById('arena-emoji').textContent = scenario.emoji;
        document.getElementById('arena-scenario-name').textContent = scenario.name;
        document.getElementById('arena-phase').textContent = '游戏进行中';

        // 更新中央区域
        const centerIcon = document.querySelector('.arena-center-icon');
        const centerText = document.querySelector('.arena-center-text');
        if (centerIcon) centerIcon.textContent = scenario.emoji || '🏟️';
        if (centerText) centerText.textContent = scenario.name + ' 进行中';

        // 启用控制按钮
        document.getElementById('btn-stop').disabled = false;

        // 隐藏再来一局
        this.playAgainBtn.classList.remove('visible');

        // 渲染围桌座位 + 底部状态栏
        if (arguments.length >= 2 && arguments[1]) {
            this.renderPlayerCards(arguments[1]);
            this._renderBottomPlayers(arguments[1]);
        }

        // 开场旁白
        this.showNarrator(`${scenario.emoji} ${scenario.name} — 对战即将开始...`);
    },

    /**
     * 渲染围桌座位卡片
     */
    renderPlayerCards(players) {
        this._players = players;
        const seatsEl = document.getElementById('arena-seats');
        if (!seatsEl) return;
        seatsEl.innerHTML = '';
        this._playerSeats = {};

        players.forEach((player, index) => {
            const charClass = this._getCharClass(player);
            const seat = Helpers.createElement('div', {
                className: `seat alive ${charClass}`,
                'data-player-id': player.id,
            });
            seat.innerHTML = `
                <div class="seat-avatar" style="--char-color: ${player.color || 'var(--color-primary)'}; border-color: ${player.color || 'var(--color-border)'};">
                    ${player.emoji || '🤖'}
                </div>
                <div class="seat-name">${Helpers.escapeHtml(player.name)}</div>
            `;
            seatsEl.appendChild(seat);
            this._playerSeats[player.id] = seat;
        });
    },

    /**
     * 渲染底部玩家状态栏
     */
    _renderBottomPlayers(players) {
        this.playersElement.innerHTML = '';
        players.forEach(player => {
            const charClass = this._getCharClass(player);
            const card = Helpers.createElement('div', {
                className: `player-card alive ${charClass}`,
                'data-player-id': player.id,
            });
            card.innerHTML = `
                <span class="player-emoji">${player.emoji || '🤖'}</span>
                <span class="player-name">${Helpers.escapeHtml(player.name)}</span>
                <span class="player-status">● 存活</span>
            `;
            this.playersElement.appendChild(card);
        });
    },

    /**
     * 显示停止确认对话框
     */
    showStopConfirm() {
        const overlay = Helpers.createElement('div', { className: 'modal-overlay' });
        overlay.innerHTML = `
            <div class="modal-box">
                <div class="modal-icon">⚠️</div>
                <h3 class="modal-title">确定要停止当前游戏吗？</h3>
                <p class="modal-desc">游戏进度将丢失，无法恢复。</p>
                <div class="modal-actions">
                    <button class="btn btn-secondary" id="modal-cancel">取消</button>
                    <button class="btn btn-danger" id="modal-confirm">停止游戏</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        overlay.querySelector('#modal-cancel').addEventListener('click', () => overlay.remove());
        overlay.querySelector('#modal-confirm').addEventListener('click', async () => {
            overlay.remove();
            await API.stopGame();
            this.addSystemEvent('游戏已停止');
        });
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });
    },

    handleEvent(event) {
        // 收到具体事件时移除思考指示
        if (event.type === 'speech' && event.player_id) {
            this.removeThinkingIndicator(event.player_id);
        }
        // 后端发送 thinking 事件时，显示思考指示
        if (event.type === 'thinking' && event.player_id) {
            this.addThinkingIndicator(event.player_id, event.player_name, event.player_emoji, event.player_color);
            this._scrollFeed();
            return;
        }

        switch (event.type) {
            case 'system':
                this.addSystemEvent(event.content);
                break;
            case 'speech':
                this.addSpeechEvent(event);
                break;
            case 'vote':
                this.addVoteEvent(event);
                break;
            case 'death':
                this.addDeathEvent(event);
                break;
            case 'phase_change':
                this.addPhaseChangeEvent(event);
                break;
            case 'game_over':
                this.addGameOverEvent(event);
                break;
            default:
                this.addSystemEvent(event.content);
        }

        // 播放音效
        if (typeof SoundFX !== 'undefined') {
            switch (event.type) {
                case 'phase_change':
                    if (event.phase === 'night') SoundFX.nightFall();
                    else if (event.phase === 'discussion') SoundFX.dayBreak();
                    else if (event.phase === 'vote') SoundFX.vote();
                    break;
                case 'speech': SoundFX.speech(); break;
                case 'death': SoundFX.death(); break;
                case 'game_over': SoundFX.victory(); break;
            }
        }

        // 更新玩家状态
        if (event.type === 'death') {
            this.updatePlayerStatus(event.player_id, false);
        }

        // 滚动到底部
        this._scrollFeed();
    },

    // ===== 旁白系统 =====

    /**
     * 显示旁白文字（打字机效果）
     */
    showNarrator(text) {
        const el = document.getElementById('narrator-text');
        if (!el) return;
        // 清除之前的打字定时器
        if (this._narratorTimeout) {
            clearTimeout(this._narratorTimeout);
            this._narratorTimeout = null;
        }
        el.textContent = '';
        el.style.borderRight = '2px solid var(--color-primary, #6366f1)';
        let i = 0;
        const type = () => {
            if (i < text.length) {
                el.textContent += text[i];
                i++;
                this._narratorTimeout = setTimeout(type, 60);
            } else {
                // 打完字后闪烁光标，3秒后消失
                this._narratorTimeout = setTimeout(() => {
                    el.style.borderRight = 'none';
                }, 3000);
            }
        };
        type();
    },

    /**
     * 清除旁白
     */
    clearNarrator() {
        if (this._narratorTimeout) {
            clearTimeout(this._narratorTimeout);
            this._narratorTimeout = null;
        }
        const el = document.getElementById('narrator-text');
        if (el) {
            el.textContent = '';
            el.style.borderRight = 'none';
        }
    },

    // ===== 围桌座位高亮 =====

    /**
     * 高亮当前发言者的座位
     */
    _highlightSpeaker(playerId) {
        // 移除所有 speaking 状态
        document.querySelectorAll('.seat.speaking').forEach(s => s.classList.remove('speaking'));
        // 高亮当前发言者
        const seat = this._playerSeats?.[playerId];
        if (seat) {
            seat.classList.add('speaking');
            // 3秒后自动移除
            setTimeout(() => seat.classList.remove('speaking'), 3000);
        }
    },

    // ===== 气泡发言系统 =====

    addSpeechEvent(event) {
        const now = Date.now();
        this._messageTimes.push(now);

        // 高亮当前发言者的座位
        this._highlightSpeaker(event.player_id);

        // 创建气泡
        const el = Helpers.createElement('div', { className: 'speech-bubble' });
        el.innerHTML = `
            <div class="speech-bubble-avatar">${event.player_emoji || '🤖'}</div>
            <div class="speech-bubble-content">
                <div class="speech-bubble-name" style="color: ${event.player_color || 'var(--color-text)'};">
                    ${Helpers.escapeHtml(event.player_name || 'AI')}
                </div>
                <div class="speech-bubble-text">${Helpers.escapeHtml(event.content)}</div>
                <div class="speech-bubble-time">${this._formatTimeAgo(now)}</div>
            </div>
        `;
        this.feedElement.appendChild(el);
        this._scrollFeed();
    },

    addSystemEvent(content) {
        const el = Helpers.createElement('div', { className: 'speech-bubble system' });
        el.innerHTML = `
            <div class="speech-bubble-content">
                <div class="speech-bubble-text">⚙️ ${Helpers.escapeHtml(content)}</div>
            </div>
        `;
        this.feedElement.appendChild(el);
        this._scrollFeed();

        // 同时更新中央区域
        const centerText = document.querySelector('.arena-center-text');
        if (centerText) centerText.textContent = content;
    },

    addVoteEvent(event) {
        const el = Helpers.createElement('div', { className: 'speech-bubble vote' });
        el.innerHTML = `
            <div class="speech-bubble-avatar">📊</div>
            <div class="speech-bubble-content">
                <div class="speech-bubble-text">${Helpers.escapeHtml(event.content)}</div>
            </div>
        `;
        this.feedElement.appendChild(el);
        this._scrollFeed();
    },

    addDeathEvent(event) {
        // 更新座位状态
        const seat = this._playerSeats?.[event.player_id];
        if (seat) {
            seat.classList.remove('alive', 'speaking', 'thinking');
            seat.classList.add('dead');
        }

        // 在发言区显示淘汰消息
        const el = Helpers.createElement('div', { className: 'speech-bubble death' });
        el.innerHTML = `
            <div class="speech-bubble-avatar">⚰️</div>
            <div class="speech-bubble-content">
                <div class="speech-bubble-text" style="color: var(--color-danger, #ef4444);">
                    ${Helpers.escapeHtml(event.content)}
                </div>
            </div>
        `;
        this.feedElement.appendChild(el);
        this._scrollFeed();

        // 更新底部状态栏
        this.updatePlayerStatus(event.player_id, false);
    },

    addPhaseChangeEvent(event) {
        // 阶段切换时移除所有思考指示和动作状态
        this.removeAllThinkingIndicators();
        this._clearAllSeatActions();

        // 更新中央区域
        const centerIcon = document.querySelector('.arena-center-icon');
        const centerText = document.querySelector('.arena-center-text');
        const phaseIcons = { 'night': '🌙', 'discussion': '☀️', 'vote': '📊' };
        if (centerIcon) centerIcon.textContent = phaseIcons[event.phase] || '🔄';
        if (centerText) centerText.textContent = event.content;

        // 更新头部
        const phaseNames = { 'night': '🌙 夜晚', 'discussion': '☀️ 白天讨论', 'vote': '📊 投票' };
        document.getElementById('arena-phase').textContent = phaseNames[event.phase] || event.phase;

        // 旁白
        const narrations = {
            'night': '🌙 夜幕降临，所有人闭上了眼睛...',
            'discussion': '☀️ 天亮了，大家开始讨论昨夜的情况...',
            'vote': '📊 投票开始，请指向你认为最可疑的人...',
        };
        this.showNarrator(narrations[event.phase] || event.content);

        // 在发言区显示阶段切换消息
        const el = Helpers.createElement('div', { className: 'speech-bubble system' });
        el.innerHTML = `
            <div class="speech-bubble-content">
                <div class="speech-bubble-text">🔄 ${Helpers.escapeHtml(event.content)}</div>
            </div>
        `;
        this.feedElement.appendChild(el);
        this._scrollFeed();

        // 阶段专属座位状态
        if (event.phase === 'night') {
            this._applyNightState();
        } else if (event.phase === 'vote') {
            this._applyVotingState();
        } else if (event.phase === 'discussion') {
            // 讨论阶段：为每个存活玩家添加思考指示
            if (this._playerSeats) {
                Object.entries(this._playerSeats).forEach(([id, seat]) => {
                    if (seat.classList.contains('alive')) {
                        const nameEl = seat.querySelector('.seat-name');
                        const avatarEl = seat.querySelector('.seat-avatar');
                        this.addThinkingIndicator(
                            id,
                            nameEl?.textContent?.trim(),
                            avatarEl?.textContent?.trim(),
                            null
                        );
                    }
                });
            }
        }
    },

    // ===== 角色动作状态 =====

    /**
     * 清除所有座位的动作状态
     */
    _clearAllSeatActions() {
        const actionClasses = ['night-hidden', 'werewolf-active', 'revealed', 'voting', 'voted', 'targeted'];
        actionClasses.forEach(cls => {
            document.querySelectorAll('.seat.' + cls).forEach(s => s.classList.remove(cls));
        });
    },

    /**
     * 夜晚状态：非狼人捂眼睛，狼人红光
     * 需要后端在 event 中携带 roles 信息，如 { player_id: 'werewolf' | 'villager' }
     * 如果没有 roles 信息，所有存活玩家都显示捂眼睛
     */
    _applyNightState() {
        if (!this._playerSeats) return;
        Object.entries(this._playerSeats).forEach(([id, seat]) => {
            if (!seat.classList.contains('alive')) return;
            // 默认全部捂眼睛；如果后端发送了角色信息，可通过 _playerRoles 判断
            if (this._playerRoles && this._playerRoles[id] === 'werewolf') {
                seat.classList.add('werewolf-active');
            } else {
                seat.classList.add('night-hidden');
            }
        });
    },

    /**
     * 投票状态：所有存活玩家显示指人动画
     */
    _applyVotingState() {
        if (!this._playerSeats) return;
        Object.entries(this._playerSeats).forEach(([id, seat]) => {
            if (!seat.classList.contains('alive')) return;
            seat.classList.add('voting');
        });
    },

    /**
     * 标记玩家已投票
     */
    markPlayerVoted(playerId) {
        const seat = this._playerSeats?.[playerId];
        if (seat) {
            seat.classList.remove('voting');
            seat.classList.add('voted');
        }
    },

    /**
     * 标记被投目标
     */
    markTargeted(playerId) {
        const seat = this._playerSeats?.[playerId];
        if (seat) {
            seat.classList.add('targeted');
        }
    },

    /**
     * 座位短暂亮起（预言家查验、医生保护等）
     */
    revealSeat(playerId, duration) {
        const seat = this._playerSeats?.[playerId];
        if (!seat) return;
        seat.classList.add('revealed');
        setTimeout(() => seat.classList.remove('revealed'), duration || 2000);
    },

    addGameOverEvent(event) {
        // 移除所有思考指示
        this.removeAllThinkingIndicators();

        // 统计
        const totalRounds = this._messageTimes.length;
        let aliveCount = 0;
        let deadCount = 0;
        if (this._playerSeats) {
            Object.values(this._playerSeats).forEach(seat => {
                if (seat.classList.contains('dead')) deadCount++;
                else aliveCount++;
            });
        }

        // 游戏结束气泡
        const el = Helpers.createElement('div', { className: 'speech-bubble game-over' });
        el.innerHTML = `
            <div class="speech-bubble-content" style="text-align: center;">
                <div style="font-size: 24px; margin-bottom: 8px;">🎉</div>
                <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">
                    ${Helpers.escapeHtml(event.content)}
                </div>
                <div style="font-size: 12px; color: var(--color-text-muted, #94a3b8); display: flex; gap: 16px; justify-content: center;">
                    <span>📊 总发言: ${totalRounds}</span>
                    <span>✅ 存活: ${aliveCount}</span>
                    <span>💀 淘汰: ${deadCount}</span>
                </div>
            </div>
        `;
        this.feedElement.appendChild(el);
        this._scrollFeed();

        // 更新中央区域
        const centerIcon = document.querySelector('.arena-center-icon');
        const centerText = document.querySelector('.arena-center-text');
        if (centerIcon) centerIcon.textContent = '🎉';
        if (centerText) centerText.textContent = '游戏结束';

        // 禁用控制按钮
        document.getElementById('btn-stop').disabled = true;
        document.getElementById('btn-pause').disabled = true;
        document.getElementById('arena-phase').textContent = '游戏结束';

        // 显示再来一局按钮
        this.playAgainBtn.classList.add('visible');
    },

    // ===== 思考指示 =====

    addThinkingIndicator(playerId, playerName, playerEmoji, playerColor) {
        // 座位思考状态
        const seat = this._playerSeats?.[playerId];
        if (seat) {
            seat.classList.add('thinking');
        }

        // 如果已存在则跳过
        if (this._thinkingIndicators[playerId]) return;

        const el = Helpers.createElement('div', { className: 'speech-bubble thinking-bubble' });
        el.setAttribute('data-thinking-id', playerId);
        el.innerHTML = `
            <div class="speech-bubble-avatar">${playerEmoji || '🤖'}</div>
            <div class="speech-bubble-content">
                <div class="speech-bubble-name" style="color: ${playerColor || 'var(--color-text)'};">
                    ${Helpers.escapeHtml(playerName || 'AI')} 正在思考
                </div>
                <div class="thinking-dots"><span>.</span><span>.</span><span>.</span></div>
            </div>
        `;
        this.feedElement.appendChild(el);
        this._thinkingIndicators[playerId] = el;
        this._scrollFeed();
    },

    removeThinkingIndicator(playerId) {
        // 移除座位思考状态
        const seat = this._playerSeats?.[playerId];
        if (seat) seat.classList.remove('thinking');

        // 移除气泡
        const el = this._thinkingIndicators[playerId];
        if (el) {
            el.remove();
            delete this._thinkingIndicators[playerId];
        }
    },

    removeAllThinkingIndicators() {
        // 移除所有座位思考状态
        document.querySelectorAll('.seat.thinking').forEach(s => s.classList.remove('thinking'));

        // 移除所有气泡
        for (const id in this._thinkingIndicators) {
            this._thinkingIndicators[id].remove();
        }
        this._thinkingIndicators = {};
    },

    // ===== 工具方法 =====

    updatePlayerStatus(playerId, isAlive) {
        // 更新座位
        const seat = this._playerSeats?.[playerId];
        if (seat && !isAlive) {
            seat.classList.remove('alive', 'speaking', 'thinking');
            seat.classList.add('dead');
        }

        // 更新底部状态栏
        const card = this.playersElement.querySelector(`[data-player-id="${playerId}"]`);
        if (card && !isAlive) {
            card.classList.remove('alive');
            card.classList.add('dead');
            const statusEl = card.querySelector('.player-status');
            if (statusEl) {
                statusEl.textContent = '● 淘汰';
                statusEl.style.color = 'var(--color-danger, #ef4444)';
            }
        }
    },

    _formatTimeAgo(timestamp) {
        const now = Date.now();
        const diff = Math.floor((now - timestamp) / 1000);
        if (diff < 5) return '刚刚';
        if (diff < 60) return `${diff}秒前`;
        if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
        return `${Math.floor(diff / 86400)}天前`;
    },

    _scrollFeed() {
        if (this.feedElement) {
            this.feedElement.scrollTop = this.feedElement.scrollHeight;
        }
    },

    scrollToBottom() {
        this._scrollFeed();
    },
};


    // ===== 字幕旁白系统 =====
    showNarrator(text) {
        const el = document.getElementById('narrator-text');
        if (!el) return;
        el.textContent = '';
        el.style.borderRight = '2px solid var(--color-primary)';
        let i = 0;
        const type = () => {
            if (i < text.length) {
                el.textContent += text[i];
                i++;
                setTimeout(type, 50);
            } else {
                setTimeout(() => { el.style.borderRight = 'none'; }, 2500);
            }
        };
        type();
    },

    // ===== 角色动作状态 =====
    setNightMode(players, wolfIds) {
        if (!this._playerSeats) return;
        Object.entries(this._playerSeats).forEach(([id, seat]) => {
            seat.classList.remove('night-hidden', 'night-revealed', 'voting', 'voted', 'targeted');
            if (wolfIds && wolfIds.includes(id)) {
                // 狼人：正常显示，加红色光效
                seat.style.filter = '';
            } else {
                seat.classList.add('night-hidden');
            }
        });
    },

    clearNightMode() {
        if (!this._playerSeats) return;
        Object.values(this._playerSeats).forEach(seat => {
            seat.classList.remove('night-hidden', 'night-revealed');
        });
    },

    setVotingMode() {
        if (!this._playerSeats) return;
        Object.values(this._playerSeats).forEach(seat => {
            if (seat.classList.contains('alive')) {
                seat.classList.add('voting');
            }
        });
    },

    markVoted(playerId) {
        const seat = this._playerSeats?.[playerId];
        if (seat) {
            seat.classList.remove('voting');
            seat.classList.add('voted');
        }
    },

    markTargeted(playerId) {
        const seat = this._playerSeats?.[playerId];
        if (seat) {
            seat.classList.add('targeted');
        }
    },

    clearVotingMode() {
        if (!this._playerSeats) return;
        Object.values(this._playerSeats).forEach(seat => {
            seat.classList.remove('voting', 'voted', 'targeted');
        });
    },

    revealPlayer(playerId) {
        const seat = this._playerSeats?.[playerId];
        if (seat) {
            seat.classList.add('night-revealed');
            setTimeout(() => seat.classList.remove('night-revealed'), 2000);
        }
    },
