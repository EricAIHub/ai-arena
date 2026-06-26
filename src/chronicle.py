"""AI Arena - 游戏编年史

每局游戏结束后生成人类可读的文字叙述，像体育解说回放。
可直接复制发朋友圈/社交媒体。
"""

from typing import Optional
import logging

arena_logger = logging.getLogger("ai_arena.chronicle")


def generate_chronicle(
    scenario: str,
    players: list,
    events: list,
    winner: str = "",
    elo_changes: dict = None,
) -> str:
    """
    生成游戏编年史。

    Args:
        scenario: 场景名称
        players: 玩家列表
        events: 游戏事件列表
        winner: 获胜方
        elo_changes: Elo 变化字典 {model: {"before": x, "after": y}}

    Returns:
        人类可读的文字叙述
    """
    lines = []

    # 标题
    emoji_map = {
        "werewolf": "🐺",
        "debate": "🗣️",
        "silly_debate": "🤡",
        "quiz": "🧠",
        "code_duel": "💻",
        "storytelling": "📖",
    }
    emoji = emoji_map.get(scenario, "🏟️")
    lines.append(f"{emoji} AI Arena 对战报告")
    lines.append("=" * 40)
    lines.append("")

    # 参赛选手
    lines.append("📋 参赛选手：")
    for p in players:
        model = getattr(p, 'model_name', '未知')
        role = getattr(p, 'role', '')
        alive = getattr(p, 'is_alive', True)
        status = "✅" if alive else "❌"
        role_text = f"（{role}）" if role else ""
        lines.append(f"  {status} {getattr(p, 'emoji', '🤖')} {p.name}{role_text} — {model}")
    lines.append("")

    # 精彩语录
    speeches = [e for e in events if e.type == "speech"]
    if speeches:
        lines.append("🎤 精彩语录：")
        # 取最有代表性的几条发言
        selected = speeches[:6] if len(speeches) > 6 else speeches
        for e in selected:
            content = e.content or ""
            # 截取前80字
            short = content[:80] + ("..." if len(content) > 80 else "")
            lines.append(f'  💬 {e.player_name}："{short}"')
        lines.append("")

    # 关键事件
    key_events = []
    for e in events:
        if e.type == "game_over":
            key_events.append(f"🏁 {e.content}")
        elif e.type == "system" and ("淘汰" in (e.content or "") or "出局" in (e.content or "")):
            key_events.append(f"💀 {e.content}")
        elif e.type == "system" and "投票" in (e.content or ""):
            key_events.append(f"🗳️ {e.content}")

    if key_events:
        lines.append("📌 关键时刻：")
        for ke in key_events[:5]:
            lines.append(f"  {ke}")
        lines.append("")

    # 结果
    lines.append("🏆 最终结果：")
    lines.append(f"  {winner}")
    lines.append("")

    # Elo 变化
    if elo_changes:
        lines.append("📊 模型积分变化：")
        for model, change in elo_changes.items():
            before = change.get("before", 1200)
            after = change.get("after", 1200)
            diff = after - before
            arrow = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
            sign = "+" if diff > 0 else ""
            lines.append(f"  {arrow} {model}: {before} → {after} ({sign}{diff})")
        lines.append("")

    # 结尾
    lines.append("=" * 40)
    lines.append("🏟️ AI Arena — AI 对战观赛平台")
    lines.append("🔗 github.com/EricAIHub/ai-arena")

    return "\n".join(lines)


def generate_share_text(
    scenario: str,
    winner: str,
    players: list,
    highlight: str = "",
) -> str:
    """
    生成简短的分享文本（适合发朋友圈/微博）。

    Args:
        scenario: 场景名称
        winner: 获胜方
        players: 玩家列表
        highlight: 一句精彩语录

    Returns:
        简短的分享文本
    """
    emoji_map = {
        "werewolf": "🐺",
        "debate": "🗣️",
        "silly_debate": "🤡",
        "quiz": "🧠",
        "code_duel": "💻",
        "storytelling": "📖",
    }
    emoji = emoji_map.get(scenario, "🏟️")

    models = list(set(getattr(p, 'model_name', '?') for p in players))
    model_str = " vs ".join(models[:3])

    text = f"{emoji} AI Arena | {model_str}\n"
    text += f"🏆 {winner}\n"
    if highlight:
        text += f'💬 "{highlight[:60]}..."\n'
    text += f"#AIArena #AI对战"

    return text
