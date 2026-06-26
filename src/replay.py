"""AI Arena - 游戏回放系统

支持完整对局 JSON 导出 + 精华摘要导出。
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime


def export_full_replay(
    scenario: str,
    players: list,
    events: list,
    winner: str = "",
    elo_changes: dict = None,
) -> dict:
    """
    导出完整对局回放。

    Returns:
        完整的回放字典，可直接 JSON 序列化
    """
    players_data = []
    for p in players:
        players_data.append({
            "id": getattr(p, "id", ""),
            "name": getattr(p, "name", ""),
            "model_name": getattr(p, "model_name", ""),
            "emoji": getattr(p, "emoji", "🤖"),
            "role": getattr(p, "role", ""),
            "personality": getattr(p, "personality", ""),
            "is_alive": getattr(p, "is_alive", True),
            "extra": getattr(p, "extra", {}),
        })

    events_data = []
    for e in events:
        ed = {
            "type": e.type,
            "player_id": e.player_id,
            "player_name": e.player_name,
            "player_emoji": e.player_emoji,
            "player_color": e.player_color,
            "content": e.content,
            "phase": e.phase,
            "data": e.data,
        }
        events_data.append(ed)

    return {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "scenario": scenario,
        "players": players_data,
        "events": events_data,
        "winner": winner,
        "elo_changes": elo_changes or {},
        "total_events": len(events_data),
        "total_speeches": len([e for e in events if e.type == "speech"]),
    }


def export_replay_summary(
    scenario: str,
    players: list,
    events: list,
    winner: str = "",
) -> dict:
    """
    导出精华摘要（适合分享）。

    Returns:
        精华摘要字典
    """
    speeches = [e for e in events if e.type == "speech"]
    key_events = [e for e in events if e.type in ("game_over", "system") and e.content]

    # 精彩语录（取前 5 条）
    highlights = []
    for s in speeches[:5]:
        content = s.content or ""
        highlights.append({
            "player": s.player_name,
            "emoji": s.player_emoji or "🤖",
            "text": content[:120] + ("..." if len(content) > 120 else ""),
        })

    # 角色分配
    roles = []
    for p in players:
        role = getattr(p, "role", "")
        alive = getattr(p, "is_alive", True)
        if role:
            roles.append({
                "name": getattr(p, "name", ""),
                "emoji": getattr(p, "emoji", "🤖"),
                "model": getattr(p, "model_name", ""),
                "role": role,
                "survived": alive,
            })

    return {
        "scenario": scenario,
        "winner": winner,
        "roles": roles,
        "highlights": highlights,
        "total_speeches": len(speeches),
        "total_events": len(events),
    }


def save_replay(replay: dict, path: str = None):
    """保存回放到文件"""
    if path is None:
        import sys
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).parent / '_internal'
        else:
            base = Path(__file__).parent.parent.parent
        path = str(base / "data" / "last_replay.json")

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(replay, f, ensure_ascii=False, indent=2)


def load_replay(path: str = None) -> Optional[dict]:
    """加载回放"""
    if path is None:
        import sys
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).parent / '_internal'
        else:
            base = Path(__file__).parent.parent.parent
        path = str(base / "data" / "last_replay.json")

    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
