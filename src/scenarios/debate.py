"""AI Arena - 辩论赛场景"""

import json
import random
from typing import Optional
from .base import (
    BaseScenario, Player, GameEvent, PhaseResult,
    GamePhase,
)
from ..ai_client import ai_client, ModelConfig, ChatMessage


# 内置话题列表
DEFAULT_TOPICS = [
    "Python vs Java 哪个更适合编程入门？",
    "AI 会取代程序员吗？",
    "远程办公比坐班更高效？",
    "开源软件比商业软件更好？",
]


class DebateScenario(BaseScenario):
    """辩论赛场景"""

    name = "辩论赛"
    description = "正方 VS 反方，三轮发言，AI 裁判评判胜负"
    min_players = 2
    max_players = 2
    emoji = "🗣️"

    def __init__(self):
        self.topic: str = ""
        self.pro_side: Optional[Player] = None   # 正方
        self.con_side: Optional[Player] = None   # 反方
        self.debate_round: int = 0                # 当前辩论轮次 (1-3)
        self.max_rounds: int = 3                  # 总轮数
        self.round_complete: bool = False         # 当前轮次是否完成
        self.game_over: bool = False

    async def setup(self, players: list[Player]) -> list[GameEvent]:
        """初始化辩论赛：选择话题、分配正反方"""
        # 随机选择话题
        self.topic = random.choice(DEFAULT_TOPICS)

        # 随机分配正反方
        shuffled = list(players)
        random.shuffle(shuffled)
        self.pro_side = shuffled[0]
        self.con_side = shuffled[1]
        self.pro_side.role = "正方"
        self.con_side.role = "反方"
        self.pro_side.extra["side"] = "pro"
        self.con_side.extra["side"] = "con"

        # 重置状态
        self.debate_round = 0
        self.round_complete = False
        self.game_over = False

        events = [
            GameEvent(
                type="system",
                content="🗣️ 辩论赛开始！",
            ),
            GameEvent(
                type="system",
                content=f"📋 辩题：{self.topic}",
            ),
            GameEvent(
                type="system",
                content=(
                    f"🔴 正方：{self.pro_side.emoji} {self.pro_side.name}\n"
                    f"🔵 反方：{self.con_side.emoji} {self.con_side.name}"
                ),
            ),
            GameEvent(
                type="system",
                content="⚖️ 规则：共 3 轮发言，正反方交替发言，最后由 AI 裁判评判胜负。",
            ),
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
            # SETUP 阶段已在 setup() 中处理，直接进入讨论
            return PhaseResult(events=[], next_phase=GamePhase.DAY_DISCUSSION)

        if phase == GamePhase.DAY_DISCUSSION:
            # 进入下一轮
            self.debate_round += 1
            events.append(GameEvent(
                type="phase_change",
                phase="discussion",
                content=f"📢 第 {self.debate_round}/{self.max_rounds} 轮发言开始！",
            ))

            # 正方先发言
            pro_prompt = await self.get_ai_prompt(self.pro_side, GamePhase.DAY_DISCUSSION, history + events)
            pro_speech = await self._get_ai_speech(self.pro_side, pro_prompt)
            events.append(GameEvent(
                type="speech",
                player_id=self.pro_side.id,
                player_name=self.pro_side.name,
                player_emoji=self.pro_side.emoji,
                player_color=self.pro_side.color,
                content=pro_speech,
                data={"side": "pro", "round": self.debate_round},
            ))

            # 反方发言（能看到正方本轮发言）
            con_prompt = await self.get_ai_prompt(self.con_side, GamePhase.DAY_DISCUSSION, history + events)
            con_speech = await self._get_ai_speech(self.con_side, con_prompt)
            events.append(GameEvent(
                type="speech",
                player_id=self.con_side.id,
                player_name=self.con_side.name,
                player_emoji=self.con_side.emoji,
                player_color=self.con_side.color,
                content=con_speech,
                data={"side": "con", "round": self.debate_round},
            ))

            # 判断是否进入裁判阶段
            if self.debate_round >= self.max_rounds:
                return PhaseResult(events=events, next_phase=GamePhase.RESULT)
            else:
                return PhaseResult(events=events, next_phase=GamePhase.DAY_DISCUSSION)

        if phase == GamePhase.RESULT:
            # ── 辩论总结阶段 ──────────────────────────────────────
            events.append(GameEvent(
                type="phase_change",
                phase="result",
                content="📝 辩论总结阶段！双方发表结辩陈词...",
            ))

            # 正方结辩
            pro_summary_prompt = self._build_summary_prompt(self.pro_side, "pro", history + events)
            pro_summary = await self._get_ai_speech(self.pro_side, pro_summary_prompt)
            events.append(GameEvent(
                type="speech",
                player_id=self.pro_side.id,
                player_name=self.pro_side.name,
                player_emoji=self.pro_side.emoji,
                player_color=self.pro_side.color,
                content=pro_summary,
                data={"side": "pro", "round": "summary"},
            ))

            # 反方结辩
            con_summary_prompt = self._build_summary_prompt(self.con_side, "con", history + events)
            con_summary = await self._get_ai_speech(self.con_side, con_summary_prompt)
            events.append(GameEvent(
                type="speech",
                player_id=self.con_side.id,
                player_name=self.con_side.name,
                player_emoji=self.con_side.emoji,
                player_color=self.con_side.color,
                content=con_summary,
                data={"side": "con", "round": "summary"},
            ))

            # 裁判评判
            events.append(GameEvent(
                type="phase_change",
                phase="judge",
                content="⚖️ 结辩完毕，有请裁判评判...",
            ))

            judge_prompt = await self._build_judge_prompt(history + events)
            judge_result = await self._get_judge_verdict(judge_prompt)
            events.append(GameEvent(
                type="system",
                content=f"⚖️ 裁判评语：\n{judge_result['comment']}",
            ))
            events.append(GameEvent(
                type="game_over",
                content=f"🏆 辩论赛结束！胜方：{judge_result['winner']}",
                data={"winner": judge_result["winner"], "winner_side": judge_result["winner_side"]},
            ))

            self.game_over = True
            return PhaseResult(
                events=events,
                next_phase=GamePhase.GAME_OVER,
                game_over=True,
                winner=judge_result["winner"],
            )

        return PhaseResult(events=[], next_phase=GamePhase.GAME_OVER)

    async def check_win_condition(self, players: list[Player]) -> Optional[str]:
        """辩论赛胜负由裁判判定，不由自动条件触发"""
        if self.game_over:
            return "裁判已判定"
        return None

    async def get_ai_prompt(
        self,
        player: Player,
        phase: GamePhase,
        history: list[GameEvent],
    ) -> str:
        """为辩手生成当前阶段的 prompt"""
        side = player.extra.get("side", "")
        side_label = "正方" if side == "pro" else "反方"
        stance = f"支持" if side == "pro" else "反对"

        # 获取可见信息
        visible = self.get_visible_info(player, history)
        history_text = "\n".join([
            f"[{e.type}] {e.player_name or ''}: {e.content}"
            for e in visible[-30:]
        ])

        if phase == GamePhase.DAY_DISCUSSION:
            return f"""你是 {player.name}，在辩论赛中担任{side_label}辩手。

辩题：{self.topic}
你的立场：{stance}该观点。

你的性格：{personality_text(player)}

辩论规则：
- 共 3 轮发言，每轮你和对手各发表一段辩论
- 你需要提出有力的论点，同时针对对方的发言进行反驳
- 语言要有说服力、逻辑严密、有理有据
- 善用具体例子、数据、类比来支撑你的观点
- 每次发言控制在 150-300 字

之前的辩论记录：
{history_text}

请发表你在第 {self.debate_round} 轮的辩论发言。
要求：
1. 提出 1-2 个新的核心论点
2. 针对对方上一轮的具体观点进行反驳
3. 用具体事例或数据支撑你的观点"""

        return ""

    # ── 内部方法 ──────────────────────────────────────────────

    async def _build_judge_prompt(self, history: list[GameEvent]) -> str:
        """构建裁判 prompt"""
        # 提取所有辩论发言
        speeches: list[str] = []
        for event in history:
            if event.type == "speech" and event.data and "side" in event.data:
                side_label = "正方" if event.data["side"] == "pro" else "反方"
                round_num = event.data.get("round", "?")
                speeches.append(f"第{round_num}轮 {side_label}({event.player_name})：{event.content}")

        all_speeches = "\n\n".join(speeches)

        return f"""你是一位公正专业的辩论裁判。

辩题：{self.topic}

以下是正方（{self.pro_side.name}）和反方（{self.con_side.name}）的辩论记录：

{all_speeches}

请从以下三个维度评判胜负：
1. 【论点质量】论点是否有力、有新意、有深度
2. 【逻辑严密性】论证过程是否严密，是否有逻辑漏洞
3. 【反驳力度】是否有效反驳了对方的观点

请严格按以下 JSON 格式回复，不要有多余内容：
{{"winner": "正方/反方", "comment": "你的详细评判（200-400字）"}}"""

    async def _get_ai_speech(self, player: Player, prompt: str) -> str:
        """获取辩手发言"""
        model = self._get_model_config(player)
        if not model:
            return f"（{player.name}：模型未配置，无法发言）"

        side = player.extra.get("side", "")
        side_label = "正方" if side == "pro" else "反方"

        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt=(
                    f"你是一位{side_label}辩手，正在进行辩论赛。"
                    f"用有力的论点和严密的逻辑进行辩论。"
                    f"每次发言控制在 150-300 字，不要暴露你是 AI。"
                ),
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.9,
                max_tokens=500,
            )
            return reply.strip()
        except Exception as e:
            return f"（{player.name}发言失败：{str(e)[:80]}）"

    async def _get_judge_verdict(self, prompt: str) -> dict:
        """获取裁判判决"""
        # 裁判使用第一个玩家的模型配置（或随机选一个）
        model = self._get_model_config(self.pro_side) or self._get_model_config(self.con_side)
        if not model:
            # Fallback: 随机判定
            winner_side = random.choice(["pro", "con"])
            winner = self.pro_side if winner_side == "pro" else self.con_side
            return {
                "winner": f"{winner.emoji} {winner.name}（{winner.role}）",
                "winner_side": winner_side,
                "comment": "（裁判模型未配置，随机判定）",
            }

        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt=(
                    "你是一位公正专业的辩论裁判。"
                    "严格按照指定的 JSON 格式回复，不要有多余内容。"
                ),
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=800,
            )
            reply = reply.strip()

            # 尝试提取 JSON 部分（处理可能的 markdown 包裹）
            json_start = reply.find("{")
            json_end = reply.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(reply[json_start:json_end])
                winner_label = result.get("winner", "")
                comment = result.get("comment", "")

                # 映射 winner 到玩家
                if "正" in winner_label:
                    winner_side = "pro"
                    winner = self.pro_side
                elif "反" in winner_label:
                    winner_side = "con"
                    winner = self.con_side
                else:
                    # 无法识别，随机
                    winner_side = random.choice(["pro", "con"])
                    winner = self.pro_side if winner_side == "pro" else self.con_side

                return {
                    "winner": f"{winner.emoji} {winner.name}（{winner.role}）",
                    "winner_side": winner_side,
                    "comment": comment,
                }
            else:
                # JSON 解析失败，随机判定
                winner_side = random.choice(["pro", "con"])
                winner = self.pro_side if winner_side == "pro" else self.con_side
                return {
                    "winner": f"{winner.emoji} {winner.name}（{winner.role}）",
                    "winner_side": winner_side,
                    "comment": reply[:400] if reply else "（裁判回复格式异常）",
                }

        except Exception as e:
            winner_side = random.choice(["pro", "con"])
            winner = self.pro_side if winner_side == "pro" else self.con_side
            return {
                "winner": f"{winner.emoji} {winner.name}（{winner.role}）",
                "winner_side": winner_side,
                "comment": f"（裁判调用失败：{str(e)[:80]}，随机判定）",
            }

    def get_visible_info(self, player: Player, history: list[GameEvent]) -> list[GameEvent]:
        """辩论赛中所有信息对双方可见"""
        return history

    def _build_summary_prompt(self, player: Player, side: str, history: list[GameEvent]) -> str:
        """构建结辩陈词 prompt"""
        side_label = "正方" if side == "pro" else "反方"
        visible = self.get_visible_info(player, history)
        history_text = "\n".join([
            f"[{e.type}] {e.player_name or ''}: {e.content}"
            for e in visible[-30:]
        ])

        return f"""你是 {player.name}，在辩论赛中担任{side_label}辩手。

辩题：{self.topic}
你的立场：{'支持' if side == 'pro' else '反对'}该观点。

你的性格：{personality_text(player)}

现在是结辩陈词环节。请回顾整场辩论，总结你的核心论点，回应对方的关键质疑，
并给出一个有力的收尾。语言要有说服力、逻辑严密、有感染力。

之前的辩论记录：
{history_text}

请发表你的结辩陈词（200-400字）。"""


def personality_text(player: Player) -> str:
    """获取辩手性格描述"""
    if player.personality:
        return player.personality
    return "理性冷静，善于用数据和事实支撑论点"
