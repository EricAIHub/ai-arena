"""AI Arena - AI 名人堂

基于 Elo 排名生成模型排行榜展示，支持分场景、分维度。
"""

import json
from pathlib import Path


# 模型展示信息（emoji + 颜色）
MODEL_PRESETS = {
    "deepseek": {"emoji": "🧊", "color": "#0066ff", "tagline": "性价比之王"},
    "gpt": {"emoji": "🤖", "color": "#10a37f", "tagline": "全能选手"},
    "gpt-4": {"emoji": "🤖", "color": "#10a37f", "tagline": "推理怪兽"},
    "gpt-5": {"emoji": "🤖", "color": "#10a37f", "tagline": "最强王者"},
    "claude": {"emoji": "🎯", "color": "#cc785c", "tagline": "理性派"},
    "anthropic": {"emoji": "🎯", "color": "#cc785c", "tagline": "安全第一"},
    "kimi": {"emoji": "🌙", "color": "#ff6b35", "tagline": "长文之王"},
    "moonshot": {"emoji": "🌙", "color": "#ff6b35", "tagline": "国产新秀"},
    "qwen": {"emoji": "🌟", "color": "#615ced", "tagline": "阿里力作"},
    "glm": {"emoji": "🔮", "color": "#4a90d9", "tagline": "智谱清言"},
    "zhipu": {"emoji": "🔮", "color": "#4a90d9", "tagline": "智谱清言"},
    "gemini": {"emoji": "✨", "color": "#4285f4", "tagline": "Google出品"},
    "grok": {"emoji": "🚀", "color": "#ff4500", "tagline": "马斯克の崽"},
}


def get_model_preset(model_name: str) -> dict:
    """获取模型展示信息"""
    name_lower = model_name.lower()
    for key, preset in MODEL_PRESETS.items():
        if key in name_lower:
            return preset
    return {"emoji": "🤖", "color": "#666666", "tagline": "神秘选手"}


def generate_hall_of_fame(scenario: str = "overall", limit: int = 10) -> dict:
    """
    生成名人堂数据。

    Args:
        scenario: 场景筛选
        limit: 显示数量

    Returns:
        名人堂数据字典
    """
    import sys
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent / '_internal'
    else:
        base = Path(__file__).parent.parent.parent

    elo_path = base / "data" / "elo_ratings.json"
    if not elo_path.exists():
        return {"champions": [], "total_games": 0, "total_models": 0}

    with open(elo_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 汇总每个模型的数据
    model_stats = {}
    for key, val in data.items():
        parts = key.split(":", 1)
        if len(parts) != 2:
            continue
        s, m = parts
        if scenario != "overall" and s != scenario:
            continue
        if m not in model_stats:
            preset = get_model_preset(m)
            model_stats[m] = {
                "model": m,
                "emoji": preset["emoji"],
                "color": preset["color"],
                "tagline": preset["tagline"],
                "elo": 0,
                "wins": 0,
                "losses": 0,
                "games": 0,
                "scenarios": [],
            }
        ms = model_stats[m]
        ms["elo"] = max(ms["elo"], val.get("elo", 1200))
        ms["wins"] += val.get("wins", 0)
        ms["losses"] += val.get("losses", 0)
        ms["games"] += val.get("wins", 0) + val.get("losses", 0) + val.get("draws", 0)
        if s not in ms["scenarios"]:
            ms["scenarios"].append(s)

    # 计算胜率并排序
    champions = list(model_stats.values())
    for c in champions:
        c["win_rate"] = round(c["wins"] / c["games"] * 100, 1) if c["games"] > 0 else 0.0
    champions.sort(key=lambda x: x["elo"], reverse=True)

    total_games = sum(c["games"] for c in champions)

    return {
        "champions": champions[:limit],
        "total_games": total_games,
        "total_models": len(champions),
    }


def get_champion_card(champion: dict) -> str:
    """
    生成冠军展示卡文本（适合分享）。

    Args:
        champion: 名人堂条目

    Returns:
        格式化的展示卡文本
    """
    medal = "🥇"
    lines = [
        f"{medal} AI Arena 名人堂",
        "=" * 30,
        "",
        f'{champion["emoji"]} {champion["model"]}',
        f'  "{champion["tagline"]}"',
        "",
        f'  Elo: {champion["elo"]}',
        f'  胜率: {champion["win_rate"]}%',
        f'  场次: {champion["games"]} ({champion["wins"]}胜 {champion["losses"]}负)',
        f'  擅长: {", ".join(champion.get("scenarios", []))}',
        "",
        "=" * 30,
        "AI Arena — AI 对战观赛平台",
    ]
    return "\n".join(lines)
