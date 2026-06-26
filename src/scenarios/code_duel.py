"""AI Arena - 代码对决场景"""

import json
import random
import re
from typing import Optional
from .base import (
    BaseScenario, Player, GameEvent, PhaseResult,
    GamePhase,
)
from ..ai_client import ai_client, ModelConfig, ChatMessage


# ── 内置编程题库 ──────────────────────────────────────────

CHALLENGE_BANK = [
    {
        "title": "两数之和",
        "description": (
            "给定一个整数数组 nums 和一个目标值 target，"
            "找出数组中和为目标值的两个数的索引。\n"
            "假设每个输入恰好有一个解，且同一个元素不能使用两次。\n\n"
            "示例：\n"
            "输入: nums = [2, 7, 11, 15], target = 9\n"
            "输出: [0, 1]（因为 nums[0] + nums[1] = 2 + 7 = 9）"
        ),
        "difficulty": "简单",
        "test_hint": "nums=[2,7,11,15], target=9 → [0,1]",
    },
    {
        "title": "实现快速排序",
        "description": (
            "实现一个快速排序算法，对整数数组进行升序排序。\n"
            "要求使用原地分区（in-place partition）的方式。\n\n"
            "示例：\n"
            "输入: [3, 6, 8, 10, 1, 2, 1]\n"
            "输出: [1, 1, 2, 3, 6, 8, 10]"
        ),
        "difficulty": "中等",
        "test_hint": "[3,6,8,10,1,2,1] → [1,1,2,3,6,8,10]",
    },
    {
        "title": "有效的括号",
        "description": (
            "给定一个只包含 '(', ')', '{', '}', '[', ']' 的字符串，"
            "判断字符串是否有效。\n"
            "有效字符串需满足：\n"
            "1. 左括号必须用相同类型的右括号闭合\n"
            "2. 左括号必须以正确的顺序闭合\n\n"
            "示例：\n"
            "输入: '()[]{}' → 输出: true\n"
            "输入: '([)]' → 输出: false\n"
            "输入: '{[]}' → 输出: true"
        ),
        "difficulty": "简单",
        "test_hint": "'()[]{}' → true, '([)]' → false",
    },
    {
        "title": "反转链表",
        "description": (
            "给定一个单链表，将其反转。\n"
            "要求：实现一个 ListNode 类和 reverse_list(head) 函数。\n\n"
            "示例：\n"
            "输入: 1 → 2 → 3 → 4 → 5\n"
            "输出: 5 → 4 → 3 → 2 → 1"
        ),
        "difficulty": "简单",
        "test_hint": "1→2→3→4→5 → 5→4→3→2→1",
    },
    {
        "title": "最长回文子串",
        "description": (
            "给定一个字符串 s，找到 s 中最长的回文子串。\n\n"
            "示例：\n"
            "输入: 'babad'\n"
            "输出: 'bab' 或 'aba'\n\n"
            "输入: 'cbbd'\n"
            "输出: 'bb'"
        ),
        "difficulty": "中等",
        "test_hint": "'babad' → 'bab' 或 'aba'",
    },
    {
        "title": "合并两个有序数组",
        "description": (
            "给定两个按非递减顺序排列的整数数组 nums1 和 nums2，"
            "将 nums2 合并到 nums1 中，使合并后的数组按非递减顺序排列。\n\n"
            "示例：\n"
            "nums1 = [1,2,3,0,0,0], m = 3\n"
            "nums2 = [2,5,6], n = 3\n"
            "输出: [1,2,2,3,5,6]"
        ),
        "difficulty": "简单",
        "test_hint": "[1,2,3] + [2,5,6] → [1,2,2,3,5,6]",
    },
]


class CodeDuelScenario(BaseScenario):
    """代码对决场景"""

    name = "代码对决"
    description = "同题竞赛，比比谁的代码更优雅"
    min_players = 2
    max_players = 6
    emoji = "💻"

    def __init__(self):
        self.challenge: dict = {}
        self.submissions: list[dict] = []  # [{player, code}]
        self.game_over: bool = False

    async def setup(self, players: list[Player]) -> list[GameEvent]:
        """初始化代码对决：选择题目"""
        self.challenge = random.choice(CHALLENGE_BANK)
        self.submissions = []
        self.game_over = False

        events = [
            GameEvent(type="system", content="💻 代码对决开始！"),
            GameEvent(type="system", content=f"📋 题目：{self.challenge['title']}（难度：{self.challenge['difficulty']}）"),
            GameEvent(type="system", content=f"📝 {self.challenge['description']}"),
        ]
        for p in players:
            events.append(GameEvent(type="system", content=f"{p.emoji} {p.name} 加入对决"))
        events.append(GameEvent(type="system", content="⏱️ 各位选手开始编码..."))
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
            # 每个玩家提交代码
            events.append(GameEvent(
                type="phase_change",
                phase="coding",
                content="⌨️ 编码阶段开始！每位选手提交自己的解法...",
            ))

            for player in players:
                prompt = self._build_coding_prompt(player, history + events)
                code = await self._get_ai_code(player, prompt)
                self.submissions.append({"player": player, "code": code})

                events.append(GameEvent(
                    type="speech",
                    player_id=player.id,
                    player_name=player.name,
                    player_emoji=player.emoji,
                    player_color=player.color,
                    content=f"📝 {player.name} 提交了代码：\n```\n{code[:500]}\n```",
                    data={"type": "code_submission"},
                ))

            # 进入裁判评判
            return PhaseResult(events=events, next_phase=GamePhase.RESULT)

        if phase == GamePhase.RESULT:
            # 裁判评判
            events.append(GameEvent(
                type="phase_change",
                phase="result",
                content="⚖️ 代码提交完毕，AI 裁判开始评判...",
            ))

            judge_result = await self._judge_code(players)

            # 展示每人的评价
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

            # 最终排名
            rankings = judge_result.get("rankings", [])
            if rankings:
                sorted_rankings = sorted(rankings, key=lambda x: x.get("score", 0), reverse=True)
                rank_lines = []
                for rank, r in enumerate(sorted_rankings, 1):
                    p = next((p for p in players if p.name == r.get("player")), None)
                    name = p.name if p else r.get("player", "未知")
                    emoji = p.emoji if p else "🤖"
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                    rank_lines.append(f"{medal} {emoji} {name} — {r.get('score', 0)} 分")

                events.append(GameEvent(
                    type="system",
                    content="📊 最终排名：\n" + "\n".join(rank_lines),
                ))

            winner_name = judge_result.get("winner", "未知")
            events.append(GameEvent(
                type="game_over",
                content=f"🏆 代码对决冠军：{winner_name}！",
                data={"winner": winner_name, "rankings": judge_result.get("rankings", [])},
            ))

            self.game_over = True
            return PhaseResult(
                events=events,
                next_phase=GamePhase.GAME_OVER,
                game_over=True,
                winner=winner_name,
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
        visible = self.get_visible_info(player, history)
        history_text = "\n".join([f"{e.content}" for e in visible[-15:]])

        return f"""你是 {player.name}，正在参加代码对决。

你的性格：{player.personality or '严谨高效，追求优雅代码'}

题目：{self.challenge['title']}
{self.challenge['description']}

比赛记录：
{history_text}

请写出完整的 Python 代码解法。只输出代码，不要解释。"""

    # ── 内部方法 ──────────────────────────────────────────────

    def _build_coding_prompt(self, player: Player, history: list[GameEvent]) -> str:
        """构建编码 prompt"""
        return f"""你是 {player.name}，正在参加代码对决竞赛。

你的性格：{player.personality or '严谨高效，追求优雅代码'}

题目：{self.challenge['title']}（难度：{self.challenge['difficulty']}）
{self.challenge['description']}

测试提示：{self.challenge.get('test_hint', '')}

要求：
1. 使用 Python 编写
2. 代码要完整可运行
3. 注重正确性、代码质量和效率
4. 只输出代码，用 ```python 包裹

请开始编码："""

    async def _get_ai_code(self, player: Player, prompt: str) -> str:
        """获取玩家的 AI 代码"""
        model = self._get_model_config(player)
        if not model:
            return "# 模型未配置，无法生成代码\npass"

        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt=(
                    "你是一个顶尖的编程竞赛选手。\n"
                    "编码要求：\n"
                    "- 写出完整、可运行、高效的 Python 代码\n"
                    "- 包含必要的类和函数定义\n"
                    "- 处理边界情况\n"
                    "- 使用清晰的变量命名和适当的注释\n"
                    "- 只输出代码，用 ```python 包裹，不要解释"
                ),
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.4,
                max_tokens=1500,
            )
            # 提取代码块
            code = self._extract_code(reply)
            return code.strip() if code else reply.strip()
        except Exception as e:
            return f"# 代码生成失败：{str(e)[:80]}\npass"

    def _extract_code(self, text: str) -> str:
        """从 AI 回复中提取代码块"""
        # 尝试匹配 ```python ... ``` 或 ``` ... ```
        match = re.search(r'```(?:python)?\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1)
        # 如果没有代码块，返回原文（去掉首尾非代码行）
        lines = text.strip().split('\n')
        # 过滤掉纯解释性文字
        code_lines = [l for l in lines if not l.startswith(("注意", "说明", "解释", "这里", "以上"))]
        return "\n".join(code_lines)

    async def _judge_code(self, players: list[Player]) -> dict:
        """AI 裁判评判代码"""
        model = self._get_model_config(players[0]) if players else None
        if not model:
            # Fallback: 随机排名
            shuffled = list(players)
            random.shuffle(shuffled)
            return {
                "rankings": [
                    {"player": p.name, "score": 80 - i * 10, "feedback": "（裁判模型未配置，随机排名）"}
                    for i, p in enumerate(shuffled)
                ],
                "winner": shuffled[0].name if shuffled else "无",
            }

        submissions_text = "\n\n".join([
            f"选手：{s['player'].name}\n代码：\n```python\n{s['code']}\n```"
            for s in self.submissions
        ])

        prompt = f"""你是一位公正的编程竞赛裁判。

题目：{self.challenge['title']}（难度：{self.challenge['difficulty']}）
{self.challenge['description']}

选手提交的代码：
{submissions_text}

请从以下维度评判每位选手的代码：
1. 【正确性】代码是否能正确解决问题（40分）
2. 【代码质量】可读性、命名规范、结构清晰（25分）
3. 【效率】时间/空间复杂度是否优秀（25分）
4. 【创意】是否有巧妙的解法或优雅的写法（10分）

请严格按以下 JSON 格式回复：
{{"rankings": [{{"player": "名字", "score": 数字0-100, "feedback": "评价（50-100字）"}}], "winner": "获胜者名字"}}"""

        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt="你是一位公正的编程竞赛裁判。严格按照 JSON 格式回复。",
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
            # Fallback: 随机排名
            shuffled = list(players)
            random.shuffle(shuffled)
            return {
                "rankings": [
                    {"player": p.name, "score": 70 - i * 5, "feedback": f"（裁判异常：{str(e)[:40]}）"}
                    for i, p in enumerate(shuffled)
                ],
                "winner": shuffled[0].name if shuffled else "无",
            }

    def get_visible_info(self, player: Player, history: list[GameEvent]) -> list[GameEvent]:
        """代码对决中所有信息可见"""
        return history
