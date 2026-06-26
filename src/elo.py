"""AI Arena - Elo 排名系统

基于游戏结果更新模型 Elo 评分，支持分场景、分角色统计。
数据持久化到 data/elo_ratings.json。
"""

import json
from pathlib import Path
from typing import Optional
import logging

arena_logger = logging.getLogger("ai_arena.elo")

# Elo 参数
K_FACTOR = 32  # 单局最大分数变动
DEFAULT_ELO = 1200  # 初始 Elo

# 数据文件路径
import sys
if getattr(sys, 'frozen', False):
    _BASE = Path(sys.executable).parent / '_internal'
else:
    _BASE = Path(__file__).parent.parent.parent
ELO_PATH = _BASE / "data" / "elo_ratings.json"


def _load_ratings() -> dict:
    """加载 Elo 数据"""
    if ELO_PATH.exists():
        with open(ELO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_ratings(data: dict):
    """保存 Elo 数据"""
    ELO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ELO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _expected_score(elo_a: float, elo_b: float) -> float:
    """计算 A 对 B 的预期胜率"""
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))


def get_model_rating(model_name: str, scenario: str = "overall") -> dict:
    """获取模型的 Elo 评分信息"""
    data = _load_ratings()
    key = f"{scenario}:{model_name}"
    if key not in data:
        return {
            "model": model_name,
            "scenario": scenario,
            "elo": DEFAULT_ELO,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "games": 0,
            "win_rate": 0.0,
        }
    entry = data[key]
    games = entry.get("wins", 0) + entry.get("losses", 0) + entry.get("draws", 0)
    return {
        "model": model_name,
        "scenario": scenario,
        "elo": entry.get("elo", DEFAULT_ELO),
        "wins": entry.get("wins", 0),
        "losses": entry.get("losses", 0),
        "draws": entry.get("draws", 0),
        "games": games,
        "win_rate": round(entry["wins"] / games * 100, 1) if games > 0 else 0.0,
    }


def get_leaderboard(scenario: str = "overall", limit: int = 20) -> list[dict]:
    """获取排行榜"""
    data = _load_ratings()
    entries = []
    for key, val in data.items():
        parts = key.split(":", 1)
        if len(parts) == 2:
            s, m = parts
            if scenario == "overall" or s == scenario:
                games = val.get("wins", 0) + val.get("losses", 0) + val.get("draws", 0)
                if games > 0:
                    entries.append({
                        "model": m,
                        "scenario": s,
                        "elo": val.get("elo", DEFAULT_ELO),
                        "wins": val.get("wins", 0),
                        "losses": val.get("losses", 0),
                        "games": games,
                        "win_rate": round(val["wins"] / games * 100, 1),
                    })
    # 按 Elo 降序
    entries.sort(key=lambda x: x["elo"], reverse=True)
    return entries[:limit]


def update_ratings_after_game(
    scenario: str,
    players: list,
    winner: str,
    events: list = None,
):
    """
    游戏结束后更新 Elo 评分。

    Args:
        scenario: 场景 ID (werewolf/debate/quiz/code_duel/storytelling)
        players: 玩家列表 (需要有 model_name, role, is_alive 属性)
        winner: 获胜方描述 (如 "狼人", "好人", "正方", "反方", 玩家名等)
        events: 游戏事件列表 (用于分析详细指标)
    """
    data = _load_ratings()

    # 收集参与的模型
    models_in_game = list(set(p.model_name for p in players if hasattr(p, 'model_name')))
    if not models_in_game:
        return

    # 判定每个模型的胜负
    model_results = {}  # model_name -> "win"/"loss"/"draw"
    for p in players:
        if not hasattr(p, 'model_name'):
            continue
        m = p.model_name
        if m not in model_results:
            model_results[m] = "draw"  # 默认平局

        # 根据场景类型判定
        if scenario == "werewolf":
            # 狼人杀：根据阵营判定
            if p.role == "狼人" and "狼人" in winner:
                model_results[m] = "win"
            elif p.role != "狼人" and "好人" in winner:
                model_results[m] = "win"
            elif p.role == "狼人" and "好人" in winner:
                model_results[m] = "loss"
            elif p.role != "狼人" and "狼人" in winner:
                model_results[m] = "loss"
        elif scenario == "debate":
            # 辩论赛：根据正反方判定
            side = p.extra.get("side", "") if hasattr(p, 'extra') else ""
            if ("正方" in winner and side == "pro") or ("反方" in winner and side == "con"):
                model_results[m] = "win"
            elif ("正方" in winner and side == "con") or ("反方" in winner and side == "pro"):
                model_results[m] = "loss"
        else:
            # 其他场景：玩家名包含在获胜方中
            if p.name in winner or (hasattr(p, 'is_alive') and p.is_alive and "平局" not in winner):
                model_results[m] = "win"
            elif hasattr(p, 'is_alive') and not p.is_alive:
                model_results[m] = "loss"

    # 更新 Elo
    model_list = list(model_results.keys())
    for i in range(len(model_list)):
        for j in range(i + 1, len(model_list)):
            m_a, m_b = model_list[i], model_list[j]
            r_a = model_results[m_a]
            r_b = model_results[m_b]

            # 获取当前 Elo
            key_a = f"{scenario}:{m_a}"
            key_b = f"{scenario}:{m_b}"
            if key_a not in data:
                data[key_a] = {"elo": DEFAULT_ELO, "wins": 0, "losses": 0, "draws": 0}
            if key_b not in data:
                data[key_b] = {"elo": DEFAULT_ELO, "wins": 0, "losses": 0, "draws": 0}

            elo_a = data[key_a]["elo"]
            elo_b = data[key_b]["elo"]

            # 预期胜率
            exp_a = _expected_score(elo_a, elo_b)
            exp_b = 1.0 - exp_a

            # 实际得分
            if r_a == "win":
                score_a = 1.0
            elif r_a == "loss":
                score_a = 0.0
            else:
                score_a = 0.5

            score_b = 1.0 - score_a

            # 更新 Elo
            data[key_a]["elo"] = round(elo_a + K_FACTOR * (score_a - exp_a))
            data[key_b]["elo"] = round(elo_b + K_FACTOR * (score_b - exp_b))

    # 更新胜负统计
    for m, result in model_results.items():
        key = f"{scenario}:{m}"
        if key not in data:
            data[key] = {"elo": DEFAULT_ELO, "wins": 0, "losses": 0, "draws": 0}
        data[key][result + "s"] = data[key].get(result + "s", 0) + 1

    # 同时更新 overall 排名
    for m, result in model_results.items():
        key = f"overall:{m}"
        if key not in data:
            data[key] = {"elo": DEFAULT_ELO, "wins": 0, "losses": 0, "draws": 0}
        data[key][result + "s"] = data[key].get(result + "s", 0) + 1

    _save_ratings(data)
    arena_logger.info(f"Elo 更新完成: {model_results}")
