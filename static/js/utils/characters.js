/**
 * AI Arena - 角色模型库
 * 为玩家提供预设角色，每个角色有独特的 emoji、颜色和风格
 */

const CharacterModels = {
    models: {
        warrior:    { emoji: '⚔️', name: '战士', color: '#ef4444', style: 'bold' },
        mage:       { emoji: '🧙', name: '法师', color: '#8b5cf6', style: 'mystical' },
        detective:  { emoji: '🔍', name: '侦探', color: '#3b82f6', style: 'analytical' },
        ninja:      { emoji: '🥷', name: '忍者', color: '#4b5563', style: 'stealth' },
        pirate:     { emoji: '🏴‍☠️', name: '海盗', color: '#f59e0b', style: 'bold' },
        robot:      { emoji: '🤖', name: '机器人', color: '#06b6d4', style: 'mechanical' },
        ghost:      { emoji: '👻', name: '幽灵', color: '#a78bfa', style: 'ethereal' },
        knight:     { emoji: '🛡️', name: '骑士', color: '#22c55e', style: 'noble' },
        wizard:     { emoji: '🪄', name: '巫师', color: '#ec4899', style: 'magical' },
        assassin:   { emoji: '🗡️', name: '刺客', color: '#dc2626', style: 'dark' },
    },

    /**
     * 场景默认角色分配
     */
    scenarioDefaults: {
        'werewolf': ['warrior', 'ninja', 'detective', 'mage', 'knight', 'assassin'],
        'debate': ['detective', 'mage', 'knight', 'warrior', 'wizard', 'robot'],
        'code_battle': ['robot', 'ninja', 'mage', 'detective', 'ghost', 'warrior'],
    },

    /**
     * 获取角色
     */
    get(id) {
        return this.models[id] || this.models.robot;
    },

    /**
     * 获取所有角色列表
     */
    getAll() {
        return Object.entries(this.models).map(([id, m]) => ({ id, ...m }));
    },

    /**
     * 获取角色的 <option> HTML
     */
    getOptionsHTML(selectedId) {
        return this.getAll().map(c =>
            `<option value="${c.id}" ${c.id === selectedId ? 'selected' : ''}>${c.emoji} ${c.name}</option>`
        ).join('');
    },

    /**
     * 为场景分配默认角色
     */
    getDefaultsForScenario(scenarioId, playerCount) {
        const defaults = this.scenarioDefaults[scenarioId] || ['robot', 'mage', 'detective', 'warrior', 'ghost', 'knight'];
        const result = [];
        for (let i = 0; i < playerCount; i++) {
            result.push(defaults[i % defaults.length]);
        }
        return result;
    },
};
