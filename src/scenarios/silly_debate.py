"""AI Arena - 沙雕辩论场景

荒诞辩题 + 搞笑风格，天然适合短视频传播。
"""

import random
from typing import Optional
from .base import (
    BaseScenario, Player, GameEvent, PhaseResult,
    GamePhase,
)
from ..ai_client import ai_client, ModelConfig, ChatMessage


# 沙雕辩题列表
SILLY_TOPICS = [
    ("WiFi 和空调只能留一个，你选哪个？", "必须选WiFi", "必须选空调"),
    ("猫和路由器哪个更重要？", "猫更重要", "路由器更重要"),
    ("如果只能吃一种食物一辈子，选火锅还是烧烤？", "永远吃火锅", "永远吃烧烤"),
    ("AI 是应该叫'人工智能'还是'人工智障'？", "它是人工智能", "它是人工智障"),
    ("打游戏时队友坑你，应该骂他还是忍着？", "必须骂", "忍着别说话"),
    ("夏天穿拖鞋上班应该被允许吗？", "拖鞋是人类之光", "拖鞋是文明的倒退"),
    ("如果动物能说话，谁说的话最毒舌？", "猫最毒舌", "鹅最毒舌"),
    ("先有鸡还是先有蛋？", "必须是先有鸡", "必须是先有蛋"),
    ("外卖小哥迟到30分钟，应该给差评吗？", "必须给差评", "绝对不给差评"),
    ("AI 写的代码能比程序员写得好吗？", "AI 完胜", "程序员永远的神"),
    ("手机只剩1%的电，你先回谁消息？", "先回对象", "先回老板"),
    ("如果可以拥有一种超能力，选隐身还是飞行？", "隐身才是王道", "飞行才是自由"),
    ("早起的鸟儿有虫吃，但早起的虫儿被鸟吃，你当哪个？", "我要当鸟", "我要当虫"),
    ("过年回家被问工资，应该怎么回答？", "直接说真话", "必须往高了吹"),
    ("奶茶应该加珍珠还是加椰果？", "珍珠是灵魂", "椰果才是正义"),
    ("如果穿越回古代只能带一样东西，带手机还是带打火机？", "手机改变历史", "打火机称霸天下"),
    ("情侣之间应该看对方手机吗？", "必须看", "绝对不能看"),
    ("下雨天没带伞，跑和走哪个淋雨少？", "跑就完了", "走才是真理"),
]


class SillyDebateScenario(BaseScenario):
    """沙雕辩论赛场景"""

    name = "沙雕辩论"
    description = "荒诞辩题 + 搞笑风格，看 AI 如何一本正经地胡说八道"
    min_players = 2
    max_players = 2
    emoji = "🤡"

    def __init__(self):
        self.topic: str = ""
        self.pro_label: str = ""
        self.con_label: str = ""
        self.pro_side: Optional[Player] = None
        self.con_side: Optional[Player] = None
        self.debate_round: int = 0
        self.max_rounds: int = 3
        self.game_over: bool = False

    async def setup(self, players: list[Player]) -> list[GameEvent]:
        """初始化沙雕辩论"""
        # 随机选择辩题
        topic_data = random.choice(SILLY_TOPICS)
        self.topic = topic_data[0]
        self.pro_label = topic_data[1]
        self.con_label = topic_data[2]

        # 随机分配正反方
        shuffled = list(players)
        random.shuffle(shuffled)
        self.pro_side = shuffled[0]
        self.con_side = shuffled[1]
        self.pro_side.role = f"正方（{self.pro_label}）"
        self.con_side.role = f"反方（{self.con_label}）"
        self.pro_side.extra["side"] = "pro"
        self.con_side.extra["side"] = "con"

        self.debate_round = 0
        self.game_over = False

        events = [
            GameEvent(type="system", content="🤡 沙雕辩论赛开始！"),
            GameEvent(type="system", content=f"🔥 辩题：{self.topic}"),
            GameEvent(type="system", content=(
                f"🔴 正方（{self.pro_label}）：{self.pro_side.emoji} {self.pro_side.name}\n"
                f"🔵 反方（{self.con_label}）：{self.con_side.emoji} {self.con_side.name}"
            )),
            GameEvent(type="system", content="📢 规则：3 轮辩论 + 结辩，要求搞笑、夸张、一本正经地胡说八道！"),
        ]
        return events

    async def run_phase(
        self,
        phase: GamePhase,
        players: list[Player],
        history: list[GameEvent],
        model_configs: dict = None,
    ) -> PhaseResult:
        self._model_configs = model_configs or {}
        events: list[GameEvent] = []

        if phase == GamePhase.SETUP:
            return PhaseResult(events=[], next_phase=GamePhase.DAY_DISCUSSION)

        if phase == GamePhase.DAY_DISCUSSION:
            self.debate_round += 1
            events.append(GameEvent(
                type="phase_change",
                phase="discussion",
                content=f"📢 第 {self.debate_round}/{self.max_rounds} 轮辩论！",
            ))

            # 思考指示
            events.append(GameEvent(
                type="thinking",
                player_id=self.pro_side.id,
                player_name=self.pro_side.name,
                player_emoji=self.pro_side.emoji,
                player_color=self.pro_side.color,
                content=f"{self.pro_side.name} 正在构思搞笑论点...",
            ))

            # 正方发言
            pro_prompt = self._build_debate_prompt(self.pro_side, "pro", history + events)
            pro_speech = await self._get_ai_speech(self.pro_side, pro_prompt)
            events.append(GameEvent(
                type="speech",
                player_id=self.pro_side.id,
                player_name=self.pro_side.name,
                player_emoji=self.pro_side.emoji,
                player_color=self.pro_side.color,
                content=pro_speech,
                data={"side": "pro", "round": self.debate_round, "label": self.pro_label},
            ))

            # 思考指示
            events.append(GameEvent(
                type="thinking",
                player_id=self.con_side.id,
                player_name=self.con_side.name,
                player_emoji=self.con_side.emoji,
                player_color=self.con_side.color,
                content=f"{self.con_side.name} 正在构思反驳...",
            ))

            # 反方发言
            con_prompt = self._build_debate_prompt(self.con_side, "con", history + events)
            con_speech = await self._get_ai_speech(self.con_side, con_prompt)
            events.append(GameEvent(
                type="speech",
                player_id=self.con_side.id,
                player_name=self.con_side.name,
                player_emoji=self.con_side.emoji,
                player_color=self.con_side.color,
                content=con_speech,
                data={"side": "con", "round": self.debate_round, "label": self.con_label},
            ))

            if self.debate_round >= self.max_rounds:
                return PhaseResult(events=events, next_phase=GamePhase.RESULT)
            else:
                return PhaseResult(events=events, next_phase=GamePhase.DAY_DISCUSSION)

        if phase == GamePhase.RESULT:
            # 结辩陈词
            events.append(GameEvent(
                type="phase_change",
                phase="result",
                content="📝 结辩时间！最后的嘴炮机会！",
            ))

            # 正方结辩
            pro_summary = self._build_summary_prompt(self.pro_side, "pro", history + events)
            pro_text = await self._get_ai_speech(self.pro_side, pro_summary)
            events.append(GameEvent(
                type="speech",
                player_id=self.pro_side.id,
                player_name=self.pro_side.name,
                player_emoji=self.pro_side.emoji,
                player_color=self.pro_side.color,
                content=pro_text,
                data={"side": "pro", "round": "summary"},
            ))

            # 反方结辩
            con_summary = self._build_summary_prompt(self.con_side, "con", history + events)
            con_text = await self._get_ai_speech(self.con_side, con_summary)
            events.append(GameEvent(
                type="speech",
                player_id=self.con_side.id,
                player_name=self.con_side.name,
                player_emoji=self.con_side.emoji,
                player_color=self.con_side.color,
                content=con_text,
                data={"side": "con", "round": "summary"},
            ))

            # AI 裁判评判
            judge_prompt = self._build_judge_prompt(history + events)
            judge_result = await self._get_judge_result(judge_prompt)

            winner = judge_result.get("winner", "平局")
            reason = judge_result.get("reason", "双方都太搞笑了，裁判无法抉择")
            funny_score = judge_result.get("funny_score", "都很搞笑")

            events.append(GameEvent(
                type="system",
                content=f"⚖️ 裁判评判：{reason}",
            ))
            events.append(GameEvent(
                type="game_over",
                content=f"🎉 {winner}获胜！搞笑指数：{funny_score}",
                data={"winner": winner, "reason": reason, "funny_score": funny_score},
            ))

            self.game_over = True
            return PhaseResult(events=events, game_over=True)

        return PhaseResult(events=events, game_over=True)

    def _build_debate_prompt(self, player: Player, side: str, history: list[GameEvent]) -> str:
        """构建辩论发言 prompt"""
        side_label = self.pro_label if side == "pro" else self.con_label
        opponent_label = self.con_label if side == "pro" else self.pro_label

        prompt = f"""你正在参加一场沙雕辩论赛。

辩题：{self.topic}
你的立场：{side_label}
对手的立场：{opponent_label}

要求：
1. 你要一本正经地为自己的立场辩护，但论点要搞笑、夸张、出人意料
2. 可以引用"数据"（编的也行）、讲段子、用网络梗
3. 语气要自信、有攻击性，像一个真正的辩手
4. 控制在 150 字以内
5. 不要用"作为AI"之类的开头，直接进入角色

{self._get_history_text(history)}

请发表你的第 {self.debate_round} 轮辩论发言："""
        return prompt

    def _build_summary_prompt(self, player: Player, side: str, history: list[GameEvent]) -> str:
        """构建结辩 prompt"""
        side_label = self.pro_label if side == "pro" else self.con_label
        return f"""沙雕辩论赛进入结辩阶段！

辩题：{self.topic}
你的立场：{side_label}

要求：
1. 总结你的核心论点，用最搞笑的方式收尾
2. 可以升华主题、煽情、或者来一个神转折
3. 控制在 100 字以内
4. 要有结束感，像一个真正的结辩

{self._get_history_text(history)}

请发表你的结辩陈词："""

    def _build_judge_prompt(self, history: list[GameEvent]) -> str:
        """构建裁判 prompt"""
        return f"""你是沙雕辩论赛的裁判。请评判以下辩论。

辩题：{self.topic}
正方立场：{self.pro_label}
反方立场：{self.con_label}

{self._get_history_text(history)}

请以 JSON 格式返回评判结果：
{{
    "winner": "正方" 或 "反方" 或 "平局",
    "reason": "一句话说明为什么（要搞笑）",
    "funny_score": "给双方的搞笑指数评语"
}}

只返回 JSON，不要其他内容。"""

    async def _get_ai_speech(self, player: Player, prompt: str) -> str:
        """获取 AI 发言"""
        model = self._get_model_config(player)
        if not model:
            return f"[{player.name} 没有配置模型，无法发言]"

        try:
            response = await ai_client.chat(
                model=model,
                system_prompt=f"你是{player.name}，一个搞笑的辩论选手。你的性格是：{player.personality or '自信、幽默、能言善辩'}。你要一本正经地胡说八道。",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.9,
                max_tokens=500,
            )
            return response
        except Exception as e:
            return f"[{player.name} 的 AI 调用失败: {str(e)}]"

    async def _get_judge_result(self, prompt: str) -> dict:
        """获取裁判评判"""
        # 使用第一个可用的模型配置
        model = None
        for m in self._model_configs.values():
            model = m
            break
        if not model:
            return {"winner": "平局", "reason": "没有可用的裁判模型", "funny_score": "无法评分"}

        try:
            response = await ai_client.chat(
                model=model,
                system_prompt="你是沙雕辩论赛的裁判，公正但搞笑。只返回 JSON。",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=300,
            )
            # 解析 JSON
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # 尝试提取 JSON
                import re
                match = re.search(r'\{[^}]+\}', response, re.DOTALL)
                if match:
                    return json.loads(match.group())
                return {"winner": "平局", "reason": response[:100], "funny_score": "裁判语无伦次"}
        except Exception as e:
            return {"winner": "平局", "reason": f"裁判出错了: {str(e)}", "funny_score": "无法评分"}

    def _get_model_config(self, player: Player) -> Optional[ModelConfig]:
        """获取玩家的模型配置"""
        return self._model_configs.get(player.model_name) if self._model_configs else None

    def _get_history_text(self, history: list[GameEvent]) -> str:
        """将历史事件转为文本"""
        lines = []
        for e in history[-15:]:  # 只取最近 15 条
            if e.type == "speech":
                side = e.data.get("side", "") if hasattr(e, 'data') and e.data else ""
                label = "正方" if side == "pro" else "反方" if side == "con" else ""
                lines.append(f"[{label} {e.player_name}]: {e.content}")
            elif e.type == "system" and "辩题" in (e.content or ""):
                lines.append(e.content)
        return "\n".join(lines) if lines else "（辩论刚开始）"

    async def get_ai_prompt(self, player: Player, phase: GamePhase, history: list[GameEvent]) -> str:
        """获取 AI prompt（基类要求实现）"""
        return self._build_debate_prompt(player, player.extra.get("side", "pro"), history)

    async def check_win_condition(self, players: list[Player]) -> Optional[str]:
        """检查胜负（由 RESULT 阶段的 game_over 控制）"""
        return None
