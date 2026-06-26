"""AI Arena - 知识问答场景"""

import json
import random
from typing import Optional
from .base import (
    BaseScenario, Player, GameEvent, PhaseResult,
    GamePhase,
)
from ..ai_client import ai_client, ModelConfig, ChatMessage


# ── 内置题库 ──────────────────────────────────────────────

QUESTION_BANK = [
    # 历史
    {"category": "历史", "question": "秦始皇统一六国是在哪一年？", "answer": "公元前221年", "keywords": ["221", "前221"]},
    {"category": "历史", "question": "第二次世界大战的欧洲战场结束于哪一年？", "answer": "1945年", "keywords": ["1945"]},
    {"category": "历史", "question": "丝绸之路的起点是中国的哪座城市？", "answer": "长安（西安）", "keywords": ["长安", "西安"]},
    {"category": "历史", "question": "法国大革命爆发于哪一年？", "answer": "1789年", "keywords": ["1789"]},
    {"category": "历史", "question": "谁发明了造纸术？", "answer": "蔡伦", "keywords": ["蔡伦"]},
    # 科学
    {"category": "科学", "question": "光在真空中的速度大约是多少千米/秒？", "answer": "约30万千米/秒（299,792 km/s）", "keywords": ["30万", "299792", "299,792", "3×10^5", "3e5"]},
    {"category": "科学", "question": "人体最大的器官是什么？", "answer": "皮肤", "keywords": ["皮肤"]},
    {"category": "科学", "question": "DNA的全称是什么？", "answer": "脱氧核糖核酸", "keywords": ["脱氧核糖核酸", "deoxyribonucleic"]},
    {"category": "科学", "question": "地球上已知最硬的天然物质是什么？", "answer": "钻石（金刚石）", "keywords": ["钻石", "金刚石"]},
    {"category": "科学", "question": "水的化学式是什么？", "answer": "H₂O", "keywords": ["h2o", "H₂O"]},
    # 编程
    {"category": "编程", "question": "Python 语言的创始人是谁？", "answer": "Guido van Rossum", "keywords": ["guido", "van rossum"]},
    {"category": "编程", "question": "HTTP 状态码 404 表示什么？", "answer": "未找到（Not Found）", "keywords": ["未找到", "not found", "404"]},
    {"category": "编程", "question": "Git 中用于查看提交历史的命令是什么？", "answer": "git log", "keywords": ["git log"]},
    {"category": "编程", "question": "SQL 中用于删除表中所有数据但保留表结构的命令是什么？", "answer": "TRUNCATE TABLE（或 DELETE FROM）", "keywords": ["truncate", "delete"]},
    {"category": "编程", "question": "JavaScript 中 typeof null 的返回值是什么？", "answer": '"object"', "keywords": ["object"]},
    # 数学
    {"category": "数学", "question": "圆周率 π 的前5位小数是什么？", "answer": "3.14159", "keywords": ["3.14159"]},
    {"category": "数学", "question": "一个三角形的内角和是多少度？", "answer": "180度", "keywords": ["180"]},
    {"category": "数学", "question": "2的10次方等于多少？", "answer": "1024", "keywords": ["1024"]},
    {"category": "数学", "question": "斐波那契数列的前8个数是什么？", "answer": "1, 1, 2, 3, 5, 8, 13, 21", "keywords": ["1,1,2,3,5,8,13,21", "1 1 2 3 5 8 13 21"]},
    {"category": "数学", "question": "质数的定义是什么？请举一个大于10的质数例子。", "answer": "只能被1和自身整除的大于1的自然数，如11、13、17等", "keywords": ["11", "13", "17", "19", "23"]},
    # 常识
    {"category": "常识", "question": "世界上面积最大的国家是哪个？", "answer": "俄罗斯", "keywords": ["俄罗斯", "russia"]},
    {"category": "常识", "question": "一年有多少个节气？", "answer": "24个", "keywords": ["24"]},
    {"category": "常识", "question": "太阳系中最大的行星是哪颗？", "answer": "木星", "keywords": ["木星", "jupiter"]},
    {"category": "常识", "question": "人体正常体温大约是多少摄氏度？", "answer": "36.5-37.5℃（约37℃）", "keywords": ["36", "37"]},
    {"category": "常识", "question": "国际象棋中，哪个棋子可以斜着走任意格数？", "answer": "象（主教/Bishop）", "keywords": ["象", "主教", "bishop"]},
]


class QuizScenario(BaseScenario):
    """知识问答场景"""

    name = "知识问答"
    description = "AI 抢答竞赛，比比谁更博学"
    min_players = 2
    max_players = 6
    emoji = "🧠"

    def __init__(self):
        self.questions: list[dict] = []
        self.current_round: int = 0
        self.total_rounds: int = 10
        self.scores: dict[str, int] = {}         # player_id -> score
        self.answered_rounds: set[int] = set()    # 已出过题的轮次
        self.game_over: bool = False

    async def setup(self, players: list[Player]) -> list[GameEvent]:
        """初始化知识问答：选择题目、重置分数"""
        # 随机选 10 题
        self.questions = random.sample(QUESTION_BANK, min(self.total_rounds, len(QUESTION_BANK)))
        self.current_round = 0
        self.game_over = False
        self.scores = {p.id: 0 for p in players}

        events = [
            GameEvent(type="system", content="🧠 知识问答开始！"),
            GameEvent(type="system", content=f"📋 共 {self.total_rounds} 题，每题答对得 10 分，最快答对额外 +5 分！"),
        ]
        for p in players:
            events.append(GameEvent(type="system", content=f"{p.emoji} {p.name} 加入比赛"))
        events.append(GameEvent(type="system", content="🔔 抢答开始！"))
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
            # 每轮出一道题，所有玩家抢答
            if self.current_round >= self.total_rounds:
                return PhaseResult(events=[], next_phase=GamePhase.RESULT)

            q = self.questions[self.current_round]
            self.current_round += 1

            events.append(GameEvent(
                type="phase_change",
                phase="quiz",
                content=f"❓ 第 {self.current_round}/{self.total_rounds} 题（{q['category']}）：{q['question']}",
            ))

            # 所有玩家同时抢答（并行模拟为依次回答，记录时间顺序）
            answers: list[dict] = []  # {player, answer, order}
            for order, player in enumerate(players):
                prompt = self._build_answer_prompt(player, q, history + events)
                answer = await self._get_ai_answer(player, prompt)
                answers.append({"player": player, "answer": answer, "order": order})

                events.append(GameEvent(
                    type="speech",
                    player_id=player.id,
                    player_name=player.name,
                    player_emoji=player.emoji,
                    player_color=player.color,
                    content=f"🔔 {player.name} 抢答：{answer}",
                    data={"round": self.current_round, "order": order},
                ))

            # 裁判判定
            judge_result = await self._judge_answers(q, answers)

            # 记录得分
            for result in judge_result:
                pid = result["player_id"]
                score = result["score"]
                self.scores[pid] = self.scores.get(pid, 0) + score
                if score > 0:
                    p = next((p for p in players if p.id == pid), None)
                    name = p.name if p else pid
                    events.append(GameEvent(
                        type="system",
                        content=f"✅ {name} 答对！+{score} 分",
                    ))

            # 公布正确答案
            events.append(GameEvent(
                type="system",
                content=f"📖 正确答案：{q['answer']}",
            ))

            # 判断是否继续
            if self.current_round >= self.total_rounds:
                return PhaseResult(events=events, next_phase=GamePhase.RESULT)
            else:
                return PhaseResult(events=events, next_phase=GamePhase.DAY_DISCUSSION)

        if phase == GamePhase.RESULT:
            # 公布最终排名
            events.append(GameEvent(
                type="phase_change",
                phase="result",
                content="🏆 知识问答结束！最终排名：",
            ))

            # 按分数排序
            ranking = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
            rank_lines = []
            for rank, (pid, score) in enumerate(ranking, 1):
                p = next((p for p in players if p.id == pid), None)
                name = p.name if p else pid
                emoji = p.emoji if p else "🤖"
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                rank_lines.append(f"{medal} {emoji} {name} — {score} 分")

            events.append(GameEvent(
                type="system",
                content="\n".join(rank_lines),
            ))

            winner_id = ranking[0][0] if ranking else None
            winner = next((p for p in players if p.id == winner_id), None)
            winner_name = f"{winner.emoji} {winner.name}" if winner else "无"

            events.append(GameEvent(
                type="game_over",
                content=f"🏆 知识问答冠军：{winner_name}！",
                data={"winner": winner_name, "scores": dict(ranking)},
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
        """知识问答不靠自动胜负条件，由最终排名决定"""
        if self.game_over:
            return "排名已出"
        return None

    async def get_ai_prompt(
        self,
        player: Player,
        phase: GamePhase,
        history: list[GameEvent],
    ) -> str:
        """为玩家生成答题 prompt"""
        visible = self.get_visible_info(player, history)
        history_text = "\n".join([f"{e.content}" for e in visible[-15:]])

        return f"""你是 {player.name}，正在参加知识问答竞赛。

你的性格：{player.personality or '博学冷静，善于快速作答'}

规则：每题抢答，答对得 10 分，最快答对额外 +5 分。

比赛记录：
{history_text}

请直接回答问题，不要解释推理过程，简短作答。"""

    # ── 内部方法 ──────────────────────────────────────────────

    def _build_answer_prompt(self, player: Player, question: dict, history: list[GameEvent]) -> str:
        """构建答题 prompt"""
        visible = self.get_visible_info(player, history)
        history_text = "\n".join([f"{e.content}" for e in visible[-10:]])

        return f"""你是 {player.name}，正在参加知识问答竞赛。

你的性格：{player.personality or '博学冷静，善于快速作答'}

当前题目（{question['category']}）：
{question['question']}

规则：直接给出答案，简短准确，不要废话。

比赛记录：
{history_text}

请直接回答："""

    async def _get_ai_answer(self, player: Player, prompt: str) -> str:
        """获取玩家的 AI 回答"""
        model = self._get_model_config(player)
        if not model:
            return "（模型未配置）"

        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt=(
                    "你是一个知识渊博的问答参赛者。\n"
                    "要求：\n"
                    "- 直接给出简短准确的答案\n"
                    "- 如果不确定，给出你最有把握的答案\n"
                    "- 对于选择题，只写选项字母或内容\n"
                    "- 对于填空题，直接写答案\n"
                    "- 最多 50 字"
                ),
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=100,
            )
            return reply.strip()
        except Exception as e:
            return f"（回答失败：{str(e)[:50]}）"

    async def _judge_answers(self, question: dict, answers: list[dict]) -> list[dict]:
        """裁判判定答案正确性，返回每人得分"""
        results = []
        correct_players: list[dict] = []

        # 先用关键词匹配快速判定
        for ans in answers:
            answer_text = ans["answer"].lower()
            is_correct = False
            for kw in question.get("keywords", []):
                if kw.lower() in answer_text:
                    is_correct = True
                    break

            if is_correct:
                correct_players.append(ans)
                results.append({"player_id": ans["player"].id, "score": 10})
            else:
                results.append({"player_id": ans["player"].id, "score": 0})

        # 最快答对的额外 +5 分（order 最小的正确答案）
        if correct_players:
            fastest = min(correct_players, key=lambda x: x["order"])
            for r in results:
                if r["player_id"] == fastest["player"].id:
                    r["score"] += 5
                    break

        # 如果关键词没匹配到任何人，用 AI 裁判二次判定
        if not correct_players:
            # 检查答案是否可能正确但关键词没覆盖
            model = self._get_model_config(answers[0]["player"]) if answers else None
            if model:
                try:
                    ai_judge = await self._ai_judge_answers(question, answers, model)
                    if ai_judge:
                        return ai_judge
                except Exception:
                    pass

        return results

    async def _ai_judge_answers(self, question: dict, answers: list[dict], model: ModelConfig) -> Optional[list[dict]]:
        """AI 裁判判定答案（关键词匹配失败时的 fallback）"""
        answers_text = "\n".join([
            f"{ans['player'].name}（顺序#{ans['order']+1}）：{ans['answer']}"
            for ans in answers
        ])

        prompt = f"""你是知识问答裁判。判断以下答案是否正确。

题目：{question['question']}
标准答案：{question['answer']}

选手回答：
{answers_text}

请严格按 JSON 格式回复：
{{"results": [{{"player": "名字", "correct": true/false}}]}}"""

        try:
            reply = await ai_client.chat(
                model=model,
                system_prompt="你是公正的知识问答裁判。只判断对错，不解释。",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.1,
                max_tokens=300,
            )

            start = reply.find("{")
            end = reply.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(reply[start:end])
                ai_results = data.get("results", [])

                results = []
                correct_players = []
                for ans in answers:
                    ai_match = next((r for r in ai_results if r.get("player") == ans["player"].name), None)
                    is_correct = ai_match.get("correct", False) if ai_match else False
                    if is_correct:
                        correct_players.append(ans)
                        results.append({"player_id": ans["player"].id, "score": 10})
                    else:
                        results.append({"player_id": ans["player"].id, "score": 0})

                # 最快答对 +5
                if correct_players:
                    fastest = min(correct_players, key=lambda x: x["order"])
                    for r in results:
                        if r["player_id"] == fastest["player"].id:
                            r["score"] += 5
                            break

                return results
        except Exception:
            pass

        return None

    def get_visible_info(self, player: Player, history: list[GameEvent]) -> list[GameEvent]:
        """知识问答中所有信息对所有人可见"""
        return history
