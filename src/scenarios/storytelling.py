"""AI Arena - 故事接龙场景"""

import json
import random
from typing import Optional
from .base import (
    BaseScenario, Player, GameEvent, PhaseResult,
    GamePhase,
)
from ..ai_client import ai_client, ModelConfig, ChatMessage


# ── 内置故事开头 ──────────────────────────────────────────

STORY_STARTERS = [
    "深夜，一列火车在隧道里突然停了。窗外一片漆黑，车厢里的灯也开始闪烁...",
    "我在旧书店的角落发现了一本没有作者名字的书，翻开第一页，上面写着：'找到这本书的人，请继续写下去...'",
    "地球上最后一个人独自坐在房间里，这时，忽然响起了敲门声...",
    "当我醒来时，发现自己躺在一片完全陌生的草原上，天空中有两个月亮...",
    "那个快递包裹上没有寄件人信息，只有一个标签：'请在满月之夜打开'...",
    "城市的供电系统已经瘫痪三天了。第四天清晨，我看见邻居家的窗户里透出了光...",
    "在 2147 年，人类终于发明了时间机器。但使用说明的第一条写着：'切勿回到发明日之前'...",
    "那只猫又来了。它每天下午三点准时坐在我窗台上，盯着我看。但今天，它开口说话了...",
]


class StorytellingScenario(BaseScenario):
    """故事接龙场景"""

    name = "故事接龙"
    description = "接力创作，看谁的故事最精彩"
    min_players = 3
    max_players = 6
    emoji = "📖"

    def __init__(self):
        self.story_starter: str = ""
        self.story_segments: list[dict] = []  # [{player, segment, round}]
        self.segments_per_player: int = 2
        self.current_round: int = 0
        self.total_rounds: int = 0  # segments_per_player * player_count
        self.current_player_index: int = 0
        self.game_over: bool = False

    async def setup(self, players: list[Player]) -> list[GameEvent]:
        """初始化故事接龙：选择开头"""
        self.story_starter = random.choice(STORY_STARTERS)
        self.story_segments = []
        self.segments_per_player = 2
        self.current_round = 0
        self.total_rounds = self.segments_per_player * len(players)
        self.current_player_index = 0
        self.game_over = False

        events = [
            GameEvent(type="system", content="📖 故事接龙开始！"),
            GameEvent(type="system", content=f"📝 每人接 {self.segments_per_player} 段，共 {self.total_rounds} 轮"),
            GameEvent(type="system", content=f"🎭 故事开头：\n「{self.story_starter}」"),
        ]
        for p in players:
            events.append(GameEvent(type="system", content=f"{p.emoji} {p.name} 加入接龙"))
        events.append(GameEvent(type="system", content="✏️ 接龙开始！第一位选手请续写..."))
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
            # 轮流接龙
            if self.current_round >= self.total_rounds:
                return PhaseResult(events=[], next_phase=GamePhase.RESULT)

            # 确定当前玩家（循环轮流）
            player = players[self.current_player_index % len(players)]
            self.current_round += 1

            round_num = self.current_round
            events.append(GameEvent(
                type="phase_change",
                phase="storytelling",
                content=f"📖 第 {round_num}/{self.total_rounds} 段 — 轮到 {player.emoji} {player.name}",
            ))

            # 获取完整故事上下文
            story_so_far = self._get_story_context()

            # AI 续写
            prompt = self._build_writing_prompt(player, story_so_far, history + events)
            segment = await self._get_ai_writing(player, prompt)

            self.story_segments.append({
                "player": player,
                "segment": segment,
                "round": round_num,
            })

            events.append(GameEvent(
                type="speech",
                player_id=player.id,
                player_name=player.name,
                player_emoji=player.emoji,
                player_color=player.color,
                content=segment,
                data={"round": round_num, "type": "story_segment"},
            ))

            # 移到下一位玩家
            self.current_player_index += 1

            # 判断是否结束
            if self.current_round >= self.total_rounds:
                return PhaseResult(events=events, next_phase=GamePhase.RESULT)
            else:
                return PhaseResult(events=events, next_phase=GamePhase.DAY_DISCUSSION)

        if phase == GamePhase.RESULT:
            # 完整故事 + 裁判评判
            events.append(GameEvent(
                type="phase_change",
                phase="result",
                content="📖 故事接龙完成！完整故事如下：",
            ))

            # 展示完整故事
            full_story = self._get_full_story()
            events.append(GameEvent(
                type="system",
                content=full_story,
            ))

            # AI 裁判评判
            events.append(GameEvent(
                type="system",
                content="⚖️ AI 裁判开始评判最佳片段...",
            ))

            judge_result = await self._judge_story(players)

            # 展示评价
            for ranking in judge_result.get("rankings", []):
                p = next((p for p in players if p.name == ranking.get("player")), None)
                name = p.name if p else ranking.get("player", "未知")
                emoji = p.emoji if p else "🤖"
                events.append(GameEvent(
                    type="system",
                    content=(
                        f"{emoji} {name} — 得分：{ranking.get('score', 0)}/100\n"
                        f"   评语：{ranking.get('feedback', '无')}"
                    ),
                ))

            # 最佳片段
            best = judge_result.get("best_segment", "未知")
            events.append(GameEvent(
                type="game_over",
                content=f"🏆 故事接龙结束！最佳片段作者：{best}",
                data={"winner": best, "rankings": judge_result.get("rankings", [])},
            ))

            self.game_over = True
            return PhaseResult(
                events=events,
                next_phase=GamePhase.GAME_OVER,
                game_over=True,
                winner=best,
            )

        return PhaseResult(events=[], next_phase=GamePhase.GAME_OVER)

    async def check_win_condition(self, players: list[Player]) -> Optional[str]:
        if self.game_over:
            return "裁判已判定"
        return None

    async def get_ai_prompt(
        self,
        player: Player,
        phase: GamePhase,
        history: list[GameEvent],
    ) -> str:
        story_so_far = self._get_story_context()
        visible = self.get_visible_info(player, history)
        history_text = "\n".join([f"{e.content}" for e in visible[-10:]])

        return f"""你是 {player.name}，正在参加故事接龙。

你的写作风格：{player.personality or '想象力丰富，文笔优美'}

故事到目前为止：
{story_so_far}

比赛记录：
{history_text}

请续写下一段故事（100-200字），要与前文自然衔接，有创意。"""

    # ── 内部方法 ──────────────────────────────────────────────

    def _build_writing_prompt(self, player: Player, story_so_far: str, history: list[GameEvent]) -> str:
        """构建续写 prompt"""
        return f"""你是 {player.name}，正在参加故事接龙竞赛。

你的写作风格：{player.personality or '想象力丰富，文笔优美'}

故事开头：
「{self.story_starter}」

到目前为止的故事：
{story_so_far}

现在轮到你续写下一段。

规则：
1. 与前文自然衔接，不要断裂
2. 推进情节发展，制造悬念或转折
3. 语言生动，有画面感
4. 字数控制在 100-200 字
5. 直接写故事内容，不要加标题或作者注释

请续写："""

    def _get_story_context(self) -> str:
        """获取当前故事全文"""
        if not self.story_segments:
            return "（故事刚开始，还没有人续写）"
        lines = []
        for seg in self.story_segments:
            p = seg["player"]
            lines.append(f"【{p.name}】{seg['segment']}")
        return "\n\n".join(lines)

    def _get_full_story(self) -> str:
        """获取完整故事（含开头）"""
        parts = [f"「{self.story_starter}」"]
        for seg in self.story_segments:
            p = seg["player"]
            parts.append(f"\n\n—— {p.emoji} {p.name} ——\n{seg['segment']}")
        return "".join(parts)

    async def _get_ai_writing(self, player: Player, prompt: str) -> str:
        """获取玩家的 AI 续写"""
        model = self._get_model_config(player)
        if not model:
            return "（模型未配置，无法续写）"

        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt=(
                    "你是一个才华横溢的故事接龙参赛者。\n"
                    "写作要求：\n"
                    "- 续写精彩的故事片段，语言生动有画面感\n"
                    "- 与前文自然衔接，推动情节发展\n"
                    "- 制造悬念、转折或情感共鸣\n"
                    "- 塑造鲜活的角色形象\n"
                    "- 控制在 100-200 字\n"
                    "- 直接写故事内容，不要加标题或作者注释"
                ),
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.95,
                max_tokens=400,
            )
            return reply.strip()
        except Exception as e:
            return f"（续写失败：{str(e)[:80]}）"

    async def _judge_story(self, players: list[Player]) -> dict:
        """AI 裁判评判故事接龙"""
        model = self._get_model_config(players[0]) if players else None
        if not model:
            # Fallback
            return {
                "rankings": [
                    {"player": p.name, "score": 80 - i * 5, "feedback": "（裁判模型未配置）"}
                    for i, p in enumerate(players)
                ],
                "best_segment": players[0].name if players else "无",
            }

        segments_text = "\n\n".join([
            f"【{seg['player'].name}】（第{seg['round']}段）：\n{seg['segment']}"
            for seg in self.story_segments
        ])

        prompt = f"""你是一位文学评审。请评判以下故事接龙作品。

故事开头：
「{self.story_starter}」

各选手续写的片段：
{segments_text}

请从以下维度评判每位选手：
1. 【创意】是否有新意、出人意料的情节（25分）
2. 【连贯性】是否与前文自然衔接（25分）
3. 【文采】语言表达是否精彩、有画面感（25分）
4. 【趣味性】是否吸引人、有悬念或感染力（25分）

请严格按以下 JSON 格式回复：
{{"rankings": [{{"player": "名字", "score": 数字0-100, "feedback": "评价（50-100字）"}}], "best_segment": "最佳片段作者名字"}}"""

        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt="你是一位公正的文学评审。严格按照 JSON 格式回复。",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=1200,
            )

            start = reply.find("{")
            end = reply.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(reply[start:end])
                return result
            else:
                raise ValueError("无法解析 JSON")

        except Exception as e:
            # Fallback
            return {
                "rankings": [
                    {"player": p.name, "score": 70 - i * 5, "feedback": f"（裁判异常：{str(e)[:40]}）"}
                    for i, p in enumerate(players)
                ],
                "best_segment": players[0].name if players else "无",
            }

    def get_visible_info(self, player: Player, history: list[GameEvent]) -> list[GameEvent]:
        """故事接龙中所有信息可见"""
        return history
