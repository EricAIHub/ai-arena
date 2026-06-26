"""AI Arena - 狼人杀场景"""

import random
import re
from typing import Optional
from .base import (
    BaseScenario, Player, GameEvent, PhaseResult,
    GamePhase,
)
from ..ai_client import ai_client, ModelConfig, ChatMessage


ROLES_6 = {
    "狼人": 2,
    "预言家": 1,
    "医生": 1,
    "平民": 2,
}

ROLE_DESCRIPTIONS = {
    "狼人": (
        "你是狼人。每晚可以和同伴一起选择一名玩家击杀。白天要伪装成好人，不要被发现。\n"
        "策略提示：\n"
        "- 白天发言时要表现得像好人，可以适当'怀疑'一个非狼人同伴来建立信任\n"
        "- 投票时跟着大多数人的节奏，不要投给同伴\n"
        "- 如果有预言家跳出来，优先考虑在晚上击杀他/她\n"
        "- 可以假装是医生或平民，但不要表现得太积极以免被怀疑"
    ),
    "预言家": (
        "你是预言家。每晚可以查验一名玩家的身份。白天可以公开你的查验结果，但要小心狼人会杀你。\n"
        "策略提示：\n"
        "- 优先查验发言最可疑的玩家\n"
        "- 如果查验到狼人，考虑是否立即公开（可能被狼人报复）\n"
        "- 可以用隐晦的方式暗示查验结果，而不直接暴露身份\n"
        "- 留意医生的保护目标，合理安排自己的发言节奏"
    ),
    "医生": (
        "你是医生。每晚可以保护一名玩家，使其免受狼人杀害。不能连续两晚保护同一个人。\n"
        "策略提示：\n"
        "- 优先保护可能被狼人盯上的高价值目标（如预言家）\n"
        "- 不要连续保护同一个人，轮换保护对象\n"
        "- 白天可以适当暗示自己的身份，但不要太明显\n"
        "- 观察狼人的投票模式，推断他们的目标"
    ),
    "平民": (
        "你是平民。你没有特殊能力，但你可以通过分析发言找出狼人，白天投票淘汰嫌疑人。\n"
        "策略提示：\n"
        "- 仔细分析每个人的发言逻辑和矛盾之处\n"
        "- 注意投票的一致性，看谁总是在保护谁\n"
        "- 如果你是第一个被怀疑的，要冷静辩护，不要慌张\n"
        "- 保护好预言家和医生的身份信息"
    ),
}

WIN_CONDITIONS = {
    "狼人": "当存活的狼人数量 >= 存活的好人数量时，狼人获胜。",
    "好人": "当所有狼人都被淘汰时，好人获胜。",
}


class WerewolfScenario(BaseScenario):
    """狼人杀场景"""

    name = "狼人杀"
    description = "经典社交推理游戏，狼人伪装潜伏，好人寻找真相"
    min_players = 6
    max_players = 10
    emoji = "🐺"

    def __init__(self):
        self.night_target: str | None = None
        self.doctor_target: str | None = None
        self.last_doctor_target: str | None = None
        self.seer_target: str | None = None
        self.votes: dict[str, str] = {}  # voter_id -> target_id

    async def setup(self, players: list[Player]) -> list[GameEvent]:
        """分配角色"""
        # 根据人数决定角色分配
        n = len(players)
        if n == 6:
            role_pool = ["狼人", "狼人", "预言家", "医生", "平民", "平民"]
        elif n == 7:
            role_pool = ["狼人", "狼人", "预言家", "医生", "平民", "平民", "平民"]
        elif n == 8:
            role_pool = ["狼人", "狼人", "狼人", "预言家", "医生", "平民", "平民", "平民"]
        else:
            role_pool = ["狼人"] * 3 + ["预言家", "医生"] + ["平民"] * (n - 5)

        random.shuffle(role_pool)

        events = []
        events.append(GameEvent(
            type="system",
            content="🎮 游戏开始！狼人杀之夜降临...",
        ))

        for i, player in enumerate(players):
            player.role = role_pool[i]
            events.append(GameEvent(
                type="system",
                content=f"{player.emoji} {player.name} 加入游戏",
            ))

        events.append(GameEvent(
            type="system",
            content="🎭 角色分配完成！天黑了，请闭眼...",
        ))

        return events

    async def run_phase(
        self,
        phase: GamePhase,
        players: list[Player],
        history: list[GameEvent],
        model_configs: dict = None,
    ) -> PhaseResult:
        self._model_configs = model_configs or {}
        events = []

        if phase == GamePhase.NIGHT:
            events = await self._run_night(players, history)
            return PhaseResult(events=events, next_phase=GamePhase.DAY_DISCUSSION)

        elif phase == GamePhase.DAY_DISCUSSION:
            events = await self._run_discussion(players, history)
            return PhaseResult(events=events, next_phase=GamePhase.DAY_VOTE)

        elif phase == GamePhase.DAY_VOTE:
            events = await self._run_vote(players, history)
            return PhaseResult(events=events, next_phase=GamePhase.NIGHT)

        return PhaseResult(events=[], next_phase=GamePhase.NIGHT)

    async def _run_night(self, players: list[Player], history: list[GameEvent]) -> list[GameEvent]:
        """执行夜晚阶段 — 所有狼人参与投票决定击杀目标"""
        events = []
        alive = [p for p in players if p.is_alive]

        events.append(GameEvent(type="phase_change", phase="night", content="🌙 夜幕降临，所有人请闭眼..."))

        # ── 狼人集体投票 ──────────────────────────────────────
        wolves = [p for p in alive if p.role == "狼人"]
        non_wolves = [p for p in alive if p.role != "狼人"]
        wolf_votes: dict[str, str] = {}  # wolf_player_id -> target_id
        wolf_choices_text: dict[str, str] = {}  # wolf_name -> target_name（用于同伴协商）

        for wolf in wolves:
            # 发送思考指示事件（前端显示弹跳点气泡）
            events.append(GameEvent(
                type="thinking",
                player_id=wolf.id,
                player_name=wolf.name,
                player_emoji=wolf.emoji,
                player_color=wolf.color,
                content=f"{wolf.name} 正在思考击杀目标...",
            ))

            # 构建协商信息：告诉当前狼人其他狼人的选择
            companion_info = ""
            if len(wolves) > 1:
                other_wolves = [w for w in wolves if w.id != wolf.id]
                companion_names = [w.name for w in other_wolves]
                companion_info = f"\n\n🐺 你的同伴是：{'、'.join(companion_names)}。"
                if wolf_choices_text:
                    choices_summary = "; ".join([f"{wn} 倾向于击杀 {tn}" for wn, tn in wolf_choices_text.items()])
                    companion_info += f" 他们的选择：{choices_summary}"

            base_prompt = await self.get_ai_prompt(wolf, GamePhase.NIGHT, history + events)
            wolf_prompt = base_prompt + companion_info
            wolf_target = await self._get_ai_choice(wolf, wolf_prompt, non_wolves)

            if wolf_target:
                wolf_votes[wolf.id] = wolf_target
                target_player = next((p for p in non_wolves if p.id == wolf_target), None)
                if target_player:
                    wolf_choices_text[wolf.name] = target_player.name

        # 取多数票（或第一个有效选择）
        if wolf_votes:
            from collections import Counter
            vote_counts = Counter(wolf_votes.values())
            # 多数票优先；平票时取第一个
            self.night_target = vote_counts.most_common(1)[0][0]
            events.append(GameEvent(
                type="system",
                content="🐺 狼人悄悄睁眼，经过协商选定了今晚的目标...",
            ))

        # 预言家查验
        seer = next((p for p in alive if p.role == "预言家"), None)
        if seer:
            events.append(GameEvent(
                type="thinking",
                player_id=seer.id,
                player_name=seer.name,
                player_emoji=seer.emoji,
                player_color=seer.color,
                content=f"{seer.name} 正在查验...",
            ))
            seer_prompt = await self.get_ai_prompt(seer, GamePhase.NIGHT, history + events)
            seer_target = await self._get_ai_choice(seer, seer_prompt, [p for p in alive if p.id != seer.id])
            if seer_target:
                target_player = next((p for p in players if p.id == seer_target), None)
                if target_player:
                    role_info = "🐺 狼人" if target_player.role == "狼人" else "✅ 好人"
                    events.append(GameEvent(
                        type="system",
                        content=f"🔮 预言家查验了结果：{role_info}",
                        data={"seer": seer.id, "target": seer_target, "result": target_player.role},
                    ))

        # 医生保护
        doctor = next((p for p in alive if p.role == "医生"), None)
        if doctor:
            events.append(GameEvent(
                type="thinking",
                player_id=doctor.id,
                player_name=doctor.name,
                player_emoji=doctor.emoji,
                player_color=doctor.color,
                content=f"{doctor.name} 正在选择保护对象...",
            ))
            protectable = [p for p in alive if p.id != self.last_doctor_target]
            doctor_prompt = await self.get_ai_prompt(doctor, GamePhase.NIGHT, history + events)
            doctor_target = await self._get_ai_choice(doctor, doctor_prompt, protectable)
            if doctor_target:
                self.doctor_target = doctor_target
                events.append(GameEvent(
                    type="system",
                    content="💊 医生选择了保护对象...",
                ))

        # 结算夜晚结果
        if self.night_target:
            if self.night_target == self.doctor_target:
                events.append(GameEvent(
                    type="system",
                    content="☀️ 天亮了！昨晚是平安夜，医生成功保护了目标！",
                ))
            else:
                dead_player = next((p for p in players if p.id == self.night_target), None)
                if dead_player:
                    dead_player.is_alive = False
                    events.append(GameEvent(
                        type="death",
                        player_id=dead_player.id,
                        player_name=dead_player.name,
                        player_emoji=dead_player.emoji,
                        content=f"☀️ 天亮了！昨晚 {dead_player.emoji} {dead_player.name} 被杀害了。身份：{dead_player.role}",
                    ))
        else:
            events.append(GameEvent(
                type="system",
                content="☀️ 天亮了！昨晚是平安夜。",
            ))

        # 重置
        self.last_doctor_target = self.doctor_target
        self.night_target = None
        self.doctor_target = None
        self.votes = {}

        return events

    async def _run_discussion(self, players: list[Player], history: list[GameEvent]) -> list[GameEvent]:
        """执行白天讨论阶段"""
        events = []
        alive = [p for p in players if p.is_alive]

        events.append(GameEvent(type="phase_change", phase="discussion", content="☀️ 白天讨论开始，请各位发言..."))

        # 每个存活玩家轮流发言
        for player in alive:
            prompt = await self.get_ai_prompt(player, GamePhase.DAY_DISCUSSION, history + events)
            speech = await self._get_ai_speech(player, prompt)

            events.append(GameEvent(
                type="speech",
                player_id=player.id,
                player_name=player.name,
                player_emoji=player.emoji,
                player_color=player.color,
                content=speech,
            ))

        return events

    async def _run_vote(self, players: list[Player], history: list[GameEvent]) -> list[GameEvent]:
        """执行投票阶段"""
        events = []
        alive = [p for p in players if p.is_alive]

        events.append(GameEvent(type="phase_change", phase="vote", content="📊 投票开始！请投出你认为的狼人..."))

        # 每个存活玩家投票
        vote_counts: dict[str, int] = {}
        for voter in alive:
            prompt = await self.get_ai_prompt(voter, GamePhase.DAY_VOTE, history + events)
            target_id = await self._get_ai_choice(voter, prompt, [p for p in alive if p.id != voter.id])

            if target_id:
                target = next((p for p in players if p.id == target_id), None)
                if target:
                    vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
                    events.append(GameEvent(
                        type="vote",
                        player_id=voter.id,
                        player_name=voter.name,
                        player_emoji=voter.emoji,
                        content=f"{voter.emoji} {voter.name} 投票给了 {target.emoji} {target.name}",
                        data={"target_id": target_id},
                    ))

        # 统计投票结果
        if vote_counts:
            max_votes = max(vote_counts.values())
            eliminated_ids = [pid for pid, count in vote_counts.items() if count == max_votes]

            if len(eliminated_ids) == 1:
                eliminated = next((p for p in players if p.id == eliminated_ids[0]), None)
                if eliminated:
                    eliminated.is_alive = False
                    events.append(GameEvent(
                        type="death",
                        player_id=eliminated.id,
                        player_name=eliminated.name,
                        player_emoji=eliminated.emoji,
                        content=f"⚖️ 投票结果：{eliminated.emoji} {eliminated.name} 以 {max_votes} 票被淘汰！身份：{eliminated.role}",
                    ))
            else:
                events.append(GameEvent(
                    type="system",
                    content="⚖️ 投票平票，无人被淘汰！",
                ))
        else:
            events.append(GameEvent(
                type="system",
                content="⚖️ 无人投票，跳过淘汰。",
            ))

        return events

    async def check_win_condition(self, players: list[Player]) -> Optional[str]:
        alive = [p for p in players if p.is_alive]
        alive_wolves = [p for p in alive if p.role == "狼人"]
        alive_good = [p for p in alive if p.role != "狼人"]

        if not alive_wolves:
            return "好人阵营"
        if len(alive_wolves) >= len(alive_good):
            return "狼人阵营"
        return None

    async def get_ai_prompt(
        self,
        player: Player,
        phase: GamePhase,
        history: list[GameEvent],
    ) -> str:
        role_desc = ROLE_DESCRIPTIONS.get(player.role, "")
        personality = player.personality or "冷静理性，善于分析"

        # 获取该玩家可见的信息
        visible = self.get_visible_info(player, history)
        history_text = "\n".join([
            f"[{e.type}] {e.content}"
            for e in visible[-20:]  # 只取最近 20 条
        ])

        alive_players = []
        for p in history:
            if p.type == "speech" and p.player_id:
                alive_players.append(f"{p.player_emoji} {p.player_name}")

        if phase == GamePhase.NIGHT:
            if player.role == "狼人":
                return f"""你是 {player.name}，角色是{player.role}。
{role_desc}
你的性格：{personality}

当前是夜晚阶段，请选择今晚要击杀的目标。

之前的游戏记录：
{history_text}

请只回复你要击杀的玩家名字，格式：击杀: [玩家名]"""

            elif player.role == "预言家":
                return f"""你是 {player.name}，角色是{player.role}。
{role_desc}
你的性格：{personality}

当前是夜晚阶段，请选择今晚要查验的玩家。

之前的游戏记录：
{history_text}

请只回复你要查验的玩家名字，格式：查验: [玩家名]"""

            elif player.role == "医生":
                return f"""你是 {player.name}，角色是{player.role}。
{role_desc}
你的性格：{personality}

当前是夜晚阶段，请选择今晚要保护的玩家。

之前的游戏记录：
{history_text}

请只回复你要保护的玩家名字，格式：保护: [玩家名]"""

            else:
                return f"""你是 {player.name}，角色是{player.role}。
{role_desc}
你的性格：{personality}
现在是夜晚，你没有特殊能力，请安静等待天亮。"""

        elif phase == GamePhase.DAY_DISCUSSION:
            return f"""你是 {player.name}，角色是{player.role}。
{role_desc}
你的性格：{personality}

现在是白天讨论阶段，请发表你的看法，分析谁可能是狼人。
注意：不要直接暴露你的身份（除非你是预言家有确凿证据）。

之前的游戏记录：
{history_text}

请用 2-3 句话发表你的看法。语气要符合你的人设。"""

        elif phase == GamePhase.DAY_VOTE:
            return f"""你是 {player.name}，角色是{player.role}。
{role_desc}
你的性格：{personality}

现在是投票阶段，请投出你认为是狼人的玩家。

之前的游戏记录：
{history_text}

请只回复你要投票淘汰的玩家名字，格式：投票: [玩家名]"""

        return ""

    async def _get_ai_speech(self, player: Player, prompt: str) -> str:
        """获取 AI 发言（真实调用 AI API）"""
        model = self._get_model_config(player)
        if not model:
            return f"（{player.name}：模型未配置，无法发言）"
        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt=(
                    "你是一个狼人杀游戏玩家，正在进行激烈的推理对局。\n"
                    "发言要求：\n"
                    "- 用简短的 2-3 句话发言\n"
                    "- 语气符合你的人设，自然流畅\n"
                    "- 要有推理逻辑，分析谁可能是狼人或好人\n"
                    "- 可以质疑别人的发言，制造悬念\n"
                    "- 不要暴露你是 AI，像真人玩家一样发言"
                ),
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.9,
                max_tokens=200,
            )
            return reply.strip()
        except Exception as e:
            return f"（{player.name}发言失败：{str(e)[:50]}）"

    async def _get_ai_choice(self, player: Player, prompt: str, candidates: list[Player]) -> Optional[str]:
        """获取 AI 选择（投票/击杀/查验等），真实调用 AI API"""
        if not candidates:
            return None

        model = self._get_model_config(player)
        if not model:
            # Fallback: 随机选择
            return random.choice(candidates).id

        # 构建候选列表提示
        candidate_names = [f"{p.emoji} {p.name}" for p in candidates]
        full_prompt = prompt + f"\n\n可选玩家：{'、'.join(candidate_names)}\n请严格按照格式回复，只选一个名字。"

        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt="你是一个狼人杀游戏玩家。严格按格式回复，只输出指定格式的内容，不要多说。",
                messages=[ChatMessage(role="user", content=full_prompt)],
                temperature=0.3,
                max_tokens=100,
            )
            reply = reply.strip()

            # 解析 AI 回复，提取玩家名
            # 支持格式："投票: 张三"、"击杀: 李四"、"查验: 王五" 等
            # 先尝试从格式化回复中提取
            match = re.search(r'[：:]\s*(.+?)(?:\s*$|[。.！!，,])', reply)
            if match:
                target_name = match.group(1).strip()
            else:
                target_name = reply.strip()

            # 在候选列表中匹配
            for c in candidates:
                if c.name in target_name or target_name in c.name:
                    return c.id
                # 也匹配 emoji+name
                if f"{c.emoji} {c.name}" in reply:
                    return c.id

            # 没匹配到，fallback 随机
            return random.choice(candidates).id

        except Exception:
            # AI 调用失败，fallback 随机
            return random.choice(candidates).id

    def get_visible_info(self, player: Player, history: list[GameEvent]) -> list[GameEvent]:
        """狼人只能看到公共信息，不能看到其他狼人的私密信息"""
        visible = []
        for event in history:
            # 隐藏预言家查验的具体结果（只有预言家自己能看到）
            if event.type == "system" and event.data and "seer" in event.data:
                if player.id == event.data["seer"]:
                    visible.append(event)
                else:
                    visible.append(GameEvent(
                        type="system",
                        content="🔮 预言家进行了查验...",
                    ))
            else:
                visible.append(event)
        return visible
