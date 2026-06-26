/**
 * AI Arena - 观战面板组件
 * 围桌对战布局：座位卡 + 气泡发言 + 阶段动效
 */

const Arena = {
    feedElement: null,
    playersElement: null,
    _players: [],
    _messageTimes: [],
    _isPaused: false,
    _thinkingIndicators: {},
    _playerSeats: {},

    init() {
        this.feedElement = document.getElementById('arena-feed');
        this.playersElement = document.getElementById('arena-players');
        this._players = [];
        this._messageTimes = [];
        this._isPaused = false;
        this._thinkingIndicators = {};
        this._playerSeats = {};
        this._blindMode = false;

        document.getElementById('btn-stop').addEventListener('click', async () => {
            await API.stopGame();
            this.addSystemEvent('游戏已停止');
        });

        document.getElementById('btn-pause').addEventListener('click', async () => {
            if (this._isPaused) {
                await API.resumeGame();
                this._isPaused = false;
                document.getElementById('btn-pause').textContent = '⏸ 暂停';
                if (typeof SoundFX !== 'undefined') SoundFX.resume();
            } else {
                await API.pauseGame();
                this._isPaused = true;
                document.getElementById('btn-pause').textContent = '▶️ 继续';
                if (typeof SoundFX !== 'undefined') SoundFX.pause();
            }
        });

        gameWS.onEvent((event) => this.handleEvent(event));
        this.setupPlayAgain();
    },

    setupPlayAgain() {
        this.playAgainBtn = document.createElement('button');
        this.playAgainBtn.id = 'btn-play-again';
        this.playAgainBtn.className = 'btn btn-primary';
        this.playAgainBtn.textContent = '🔄 再来一局';
        this.playAgainBtn.style.cssText = 'margin-top: var(--space-4); width: 100%; display: none;';
        this.playAgainBtn.addEventListener('click', () => {
            this.reset();
            App.navigateTo('scenarios');
        });
        this.feedElement.parentNode.appendChild(this.playAgainBtn);
    },

    reset() {
        this.feedElement.innerHTML = '<div class="feed-empty"><span class="feed-empty-icon">🏟️</span><p>选择场景并开始游戏后，这里将显示实时对战内容</p></div>';
        this.playersElement.innerHTML = '';
        this.playAgainBtn.style.display = 'none';
        this._players = [];
        this._messageTimes = [];
        this._isPaused = false;
        this._thinkingIndicators = {};
        this._playerSeats = {};
        this._blindMode = false;
        document.getElementById('arena-emoji').textContent = '🏟️';
        document.getElementById('arena-scenario-name').textContent = '等待开始...';
        document.getElementById('arena-phase').textContent = '';
        document.getElementById('btn-stop').disabled = true;
        document.getElementById('btn-pause').disabled = true;
        const center = document.getElementById('arena-center');
        if (center) {
            center.querySelector('.arena-center-icon').textContent = '🏟️';
            center.querySelector('.arena-center-text').textContent = '等待开始...';
        }
    },

    onGameStart(scenario, players) {
        this.feedElement.innerHTML = '';
        this._messageTimes = [];
        this._isPaused = false;
        this._thinkingIndicators = {};
        this._playerSeats = {};
        document.getElementById('arena-emoji').textContent = scenario.emoji;
        document.getElementById('arena-scenario-name').textContent = scenario.name;
        document.getElementById('arena-phase').textContent = '游戏进行中';
        document.getElementById('btn-stop').disabled = false;
        document.getElementById('btn-pause').disabled = false;
        document.getElementById('btn-pause').textContent = '⏸ 暂停';
        this.playAgainBtn.style.display = 'none';

        if (players && players.length) {
            this._players = players;
            this.renderPlayerCards(players);
            this.renderBottomPlayers(players);
        }
    },

    renderPlayerCards(players) {
        const seatsEl = document.getElementById('arena-seats');
        if (!seatsEl) return;
        seatsEl.innerHTML = '';
        this._playerSeats = {};

        players.forEach((player) => {
            const seat = document.createElement('div');
            seat.className = 'seat alive';
            seat.setAttribute('data-player-id', player.id);
            seat.innerHTML = '<div class="seat-avatar">' + (player.emoji || '🤖') + '</div><div class="seat-name">' + this._esc(player.name) + '</div>';
            seatsEl.appendChild(seat);
            this._playerSeats[player.id] = seat;
        });
    },

    renderBottomPlayers(players) {
        if (!this.playersElement) return;
        this.playersElement.innerHTML = '';
        players.forEach((p) => {
            const card = document.createElement('div');
            card.className = 'player-card alive';
            card.setAttribute('data-player-id', p.id);
            card.innerHTML = '<span class="player-emoji">' + (p.emoji || '🤖') + '</span><span class="player-name">' + this._esc(p.name) + '</span><span class="player-status">存活</span>';
            this.playersElement.appendChild(card);
        });
    },

    handleEvent(event) {
        if (event.type === 'speech' && event.player_id) this.removeThinkingIndicator(event.player_id);
        if (event.type === 'thinking' && event.player_id) {
            this.addThinkingIndicator(event.player_id, event.player_name, event.player_emoji, event.player_color);
            this.scrollToBottom();
            return;
        }

        switch (event.type) {
            case 'system': this.addSystemEvent(event.content); break;
            case 'speech': this.addSpeechEvent(event); break;
            case 'vote': this.addVoteEvent(event); break;
            case 'death': this.addDeathEvent(event); break;
            case 'phase_change': this.addPhaseChangeEvent(event); break;
            case 'game_over': this.addGameOverEvent(event); break;
            default: this.addSystemEvent(event.content);
        }

        if (event.type === 'death' && event.player_id) this.updatePlayerStatus(event.player_id, false);

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

        this.scrollToBottom();
    },

    addSpeechEvent(event) {
        this._highlightSpeaker(event.player_id);
        const time = this._formatTimeAgo(Date.now());
        const el = document.createElement('div');
        el.className = 'speech-bubble';
        el.innerHTML = '<div class="speech-bubble-avatar">' + (event.player_emoji || '🤖') + '</div><div class="speech-bubble-content"><div class="speech-bubble-name" style="color:' + (event.player_color || 'var(--color-text)') + ';">' + this._esc(event.player_name || 'AI') + '</div><div class="speech-bubble-text">' + this._esc(event.content) + '</div><div class="speech-bubble-time">' + time + '</div></div>';
        this.feedElement.appendChild(el);
        this.scrollToBottom();
    },

    addSystemEvent(content) {
        const el = document.createElement('div');
        el.className = 'speech-bubble system';
        el.innerHTML = '<div class="speech-bubble-content"><div class="speech-bubble-text">⚙️ ' + this._esc(content) + '</div></div>';
        this.feedElement.appendChild(el);
        this.scrollToBottom();
        // 更新中央区域文字（截取前50字）
        const centerText = document.querySelector('.arena-center-text');
        if (centerText) {
            const short = content.length > 50 ? content.substring(0, 50) + '...' : content;
            centerText.textContent = short;
        }
    },

    addVoteEvent(event) {
        const el = document.createElement('div');
        el.className = 'speech-bubble vote';
        el.innerHTML = '<div class="speech-bubble-content"><div class="speech-bubble-text">📊 ' + this._esc(event.content) + '</div></div>';
        this.feedElement.appendChild(el);
        this.scrollToBottom();
    },

    addDeathEvent(event) {
        const seat = this._playerSeats[event.player_id];
        if (seat) { seat.classList.remove('alive', 'speaking', 'thinking'); seat.classList.add('dead'); }
        const el = document.createElement('div');
        el.className = 'speech-bubble death';
        el.innerHTML = '<div class="speech-bubble-avatar">⚰️</div><div class="speech-bubble-content"><div class="speech-bubble-text" style="color:var(--color-danger);">' + this._esc(event.content) + '</div></div>';
        this.feedElement.appendChild(el);
        this.scrollToBottom();
        this.updatePlayerStatus(event.player_id, false);
    },

    addPhaseChangeEvent(event) {
        this.removeAllThinkingIndicators();
        const phaseIcons = { night: '🌙', discussion: '☀️', vote: '📊' };
        const phaseNames = { night: '🌙 夜晚', discussion: '☀️ 白天讨论', vote: '📊 投票' };
        const centerIcon = document.querySelector('.arena-center-icon');
        const centerText = document.querySelector('.arena-center-text');
        if (centerIcon) centerIcon.textContent = phaseIcons[event.phase] || '🔄';
        if (centerText) centerText.textContent = event.content;
        document.getElementById('arena-phase').textContent = phaseNames[event.phase] || event.phase;

        if (event.phase === 'discussion') {
            this._players.forEach(p => {
                if (p.is_alive !== false) this.addThinkingIndicator(p.id, p.name, p.emoji, p.color);
            });
        }
    },

    addGameOverEvent(event) {
        this.removeAllThinkingIndicators();
        const el = document.createElement('div');
        el.className = 'speech-bubble game-over';
        el.innerHTML = '<div class="speech-bubble-content"><div class="speech-bubble-text" style="font-size:var(--text-lg);font-weight:700;">🎉 ' + this._esc(event.content) + '</div></div>';
        this.feedElement.appendChild(el);
        // 显示统计数据
        this.showGameOverStats(event);
        document.getElementById('btn-stop').disabled = true;
        document.getElementById('btn-pause').disabled = true;
        document.getElementById('arena-phase').textContent = '游戏结束';
        this.playAgainBtn.style.display = 'block';
        this.scrollToBottom();
    },

    updatePlayerStatus(playerId, isAlive) {
        const card = this.playersElement?.querySelector('[data-player-id="' + playerId + '"]');
        if (!card) return;
        if (!isAlive) {
            card.classList.add('dead');
            card.classList.remove('alive');
            const status = card.querySelector('.player-status');
            if (status) { status.textContent = '淘汰'; status.style.color = 'var(--color-danger)'; }
        }
    },

    _highlightSpeaker(playerId) {
        document.querySelectorAll('.seat.speaking').forEach(s => s.classList.remove('speaking'));
        const seat = this._playerSeats[playerId];
        if (seat) {
            seat.classList.add('speaking');
            setTimeout(() => seat.classList.remove('speaking'), 3000);
        }
    },

    addThinkingIndicator(playerId, playerName, playerEmoji, playerColor) {
        if (this._thinkingIndicators[playerId]) return;
        const seat = this._playerSeats[playerId];
        if (seat) seat.classList.add('thinking');
        const el = document.createElement('div');
        el.className = 'speech-bubble thinking-bubble';
        el.setAttribute('data-thinking-id', playerId);
        el.innerHTML = '<div class="speech-bubble-avatar">' + (playerEmoji || '🤖') + '</div><div class="speech-bubble-content"><div class="speech-bubble-name" style="color:' + (playerColor || 'var(--color-text)') + ';">' + this._esc(playerName || 'AI') + ' 正在思考</div><div class="thinking-dots"><span>.</span><span>.</span><span>.</span></div></div>';
        this.feedElement.appendChild(el);
        this._thinkingIndicators[playerId] = el;
        this.scrollToBottom();
    },

    removeThinkingIndicator(playerId) {
        const seat = this._playerSeats[playerId];
        if (seat) seat.classList.remove('thinking');
        const el = this._thinkingIndicators[playerId];
        if (el) { el.remove(); delete this._thinkingIndicators[playerId]; }
    },

    removeAllThinkingIndicators() {
        for (const id in this._thinkingIndicators) {
            this._thinkingIndicators[id].remove();
        }
        this._thinkingIndicators = {};
        if (this._playerSeats) {
            Object.values(this._playerSeats).forEach(s => s.classList.remove('thinking'));
        }
    },

    showNarrator(text) {
        const el = document.getElementById('narrator-text');
        if (!el) return;
        el.textContent = '';
        el.style.borderRight = '2px solid var(--color-primary)';
        let i = 0;
        const type = () => {
            if (i < text.length) { el.textContent += text[i]; i++; setTimeout(type, 50); }
            else { setTimeout(() => { el.style.borderRight = 'none'; }, 2500); }
        };
        type();
    },

    setNightMode(players, wolfIds) {
        if (!this._playerSeats) return;
        Object.entries(this._playerSeats).forEach(([id, seat]) => {
            seat.classList.remove('night-hidden', 'night-revealed', 'voting', 'voted', 'targeted');
            if (wolfIds && wolfIds.includes(id)) { seat.style.filter = ''; }
            else { seat.classList.add('night-hidden'); }
        });
    },

    clearNightMode() {
        if (!this._playerSeats) return;
        Object.values(this._playerSeats).forEach(s => s.classList.remove('night-hidden', 'night-revealed'));
    },

    setVotingMode() {
        if (!this._playerSeats) return;
        Object.values(this._playerSeats).forEach(s => {
            if (s.classList.contains('alive')) s.classList.add('voting');
        });
    },

    markVoted(playerId) {
        const s = this._playerSeats[playerId];
        if (s) { s.classList.remove('voting'); s.classList.add('voted'); }
    },

    markTargeted(playerId) {
        const s = this._playerSeats[playerId];
        if (s) s.classList.add('targeted');
    },

    clearVotingMode() {
        if (!this._playerSeats) return;
        Object.values(this._playerSeats).forEach(s => s.classList.remove('voting', 'voted', 'targeted'));
    },

    revealPlayer(playerId) {
        const s = this._playerSeats[playerId];
        if (s) { s.classList.add('night-revealed'); setTimeout(() => s.classList.remove('night-revealed'), 2000); }
    },

    scrollToBottom() {
        if (this.feedElement) this.feedElement.scrollTop = this.feedElement.scrollHeight;
    },

    _esc(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },

    _formatTimeAgo(ts) {
        const sec = Math.floor((Date.now() - ts) / 1000);
        if (sec < 5) return '刚刚';
        if (sec < 60) return sec + '秒前';
        if (sec < 3600) return Math.floor(sec / 60) + '分钟前';
        return Math.floor(sec / 3600) + '小时前';
    },

    showGameOverStats(event) {
        // 游戏结束时显示统计信息
        const data = event.data || {};
        let statsHtml = '<div style="margin-top:var(--space-3);padding:var(--space-3);border-radius:var(--radius-md);background:var(--color-bg-secondary);">';
        if (data.winner) {
            statsHtml += '<div style="font-weight:600;margin-bottom:var(--space-2);">🏆 获胜方：' + this._esc(data.winner) + '</div>';
        }
        if (data.rankings && Array.isArray(data.rankings)) {
            statsHtml += '<div style="font-size:var(--text-sm);color:var(--color-text-secondary);">';
            data.rankings.forEach((r, i) => {
                const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '#' + (i+1);
                statsHtml += medal + ' ' + this._esc(r.player || '???') + ' — ' + (r.score || 0) + '分<br>';
            });
            statsHtml += '</div>';
        }
        statsHtml += '</div>';
        const el = document.createElement('div');
        el.className = 'speech-bubble system';
        el.innerHTML = '<div class="speech-bubble-content">' + statsHtml + '</div>';
        this.feedElement.appendChild(el);
    },
};
