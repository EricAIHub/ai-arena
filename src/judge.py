"""AI Arena - 裁判系统"""

from .ai_client import ai_client, ModelConfig, ChatMessage


class Judge:
    """AI 裁判 - 用于评判胜负"""

    def __init__(self, model: ModelConfig):
        self.model = model

    async def judge_debate(
        self,
        topic: str,
        pro_arguments: list[str],
        con_arguments: list[str],
    ) -> dict:
        """
        评判辩论赛胜负。

        Args:
            topic: 辩论话题
            pro_arguments: 正方论点列表
            con_arguments: 反方论点列表

        Returns:
            {
                "winner": "正方" | "反方",
                "score": {"pro": 85, "con": 78},
                "reasoning": "评判理由...",
            }
        """
        pro_text = "\n".join([f"第{i+1}轮：{arg}" for i, arg in enumerate(pro_arguments)])
        con_text = "\n".join([f"第{i+1}轮：{arg}" for i, arg in enumerate(con_arguments)])

        prompt = f"""你是一位公正的辩论裁判。请评判以下辩论的胜负。

辩论话题：{topic}

正方论点：
{pro_text}

反方论点：
{con_text}

请从以下维度评判：
1. 论点质量（是否有理有据）
2. 逻辑严密性（推理是否合理）
3. 反驳力度（是否有效回应对方）
4. 表达清晰度（是否易于理解）

请严格按照以下 JSON 格式回复，不要有其他内容：
{{"winner": "正方或反方", "pro_score": 数字0-100, "con_score": 数字0-100, "reasoning": "评判理由"}}"""

        try:
            response = await ai_client.chat(
                model=self.model,
                system_prompt="你是一位公正的辩论裁判，只根据辩论内容评判胜负。",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=500,
            )

            # 解析 JSON
            import json
            # 尝试提取 JSON
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
                return {
                    "winner": result.get("winner", "平局"),
                    "score": {
                        "pro": result.get("pro_score", 50),
                        "con": result.get("con_score", 50),
                    },
                    "reasoning": result.get("reasoning", "无法解析评判理由"),
                }
        except Exception as e:
            print(f"裁判评判失败: {e}")

        return {
            "winner": "平局",
            "score": {"pro": 50, "con": 50},
            "reasoning": "裁判系统异常，判定为平局",
        }

    async def judge_code_duel(
        self,
        challenge: str,
        submissions: list[dict],
    ) -> dict:
        """
        评判代码对决。

        Args:
            challenge: 编程题目
            submissions: [{"player": "name", "code": "code_content"}, ...]

        Returns:
            {
                "rankings": [{"player": "name", "score": 90, "feedback": "..."}],
                "winner": "name",
            }
        """
        submissions_text = "\n\n".join([
            f"选手：{s['player']}\n代码：\n```\n{s['code']}\n```"
            for s in submissions
        ])

        prompt = f"""你是一位编程竞赛裁判。请评判以下代码对决的胜负。

题目：{challenge}

选手提交：
{submissions_text}

请从以下维度评判：
1. 正确性（代码是否能正确解决问题）
2. 代码质量（可读性、规范性）
3. 效率（时间/空间复杂度）
4. 创意（是否有巧妙的解法）

请严格按照以下 JSON 格式回复：
{{"rankings": [{{"player": "名字", "score": 数字0-100, "feedback": "评价"}}], "winner": "获胜者名字"}}"""

        try:
            response = await ai_client.chat(
                model=self.model,
                system_prompt="你是一位公正的编程竞赛裁判。",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=800,
            )

            import json
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
                return result
        except Exception as e:
            print(f"裁判评判失败: {e}")

        return {
            "rankings": [{"player": s["player"], "score": 50, "feedback": "评判异常"} for s in submissions],
            "winner": submissions[0]["player"] if submissions else "无",
        }

    async def judge_storytelling(
        self,
        story_segments: list[dict],
    ) -> dict:
        """
        评判故事接龙。

        Args:
            story_segments: [{"player": "name", "segment": "text"}, ...]

        Returns:
            {
                "rankings": [{"player": "name", "score": 85, "feedback": "..."}],
                "best_segment": "name",
            }
        """
        segments_text = "\n\n".join([
            f"{s['player']}：{s['segment']}"
            for s in story_segments
        ])

        prompt = f"""你是一位文学评审。请评判以下故事接龙作品。

故事片段：
{segments_text}

请从以下维度评判：
1. 创意（是否有新意）
2. 连贯性（是否与前面衔接自然）
3. 文采（语言表达是否精彩）
4. 趣味性（是否吸引人）

请严格按照以下 JSON 格式回复：
{{"rankings": [{{"player": "名字", "score": 数字0-100, "feedback": "评价"}}], "best_segment": "最佳片段作者名字"}}"""

        try:
            response = await ai_client.chat(
                model=self.model,
                system_prompt="你是一位公正的文学评审。",
                messages=[ChatMessage(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=800,
            )

            import json
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except Exception as e:
            print(f"裁判评判失败: {e}")

        return {
            "rankings": [{"player": s["player"], "score": 50, "feedback": "评判异常"} for s in story_segments],
            "best_segment": story_segments[0]["player"] if story_segments else "无",
        }
