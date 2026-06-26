"""AI Arena - 统一日志系统

使用 Python logging 模块，日志输出到 data/arena.log。
分级：DEBUG, INFO, WARNING, ERROR。
"""

import logging
from pathlib import Path


# 日志文件路径
LOG_DIR = Path(__file__).parent.parent / "data"
LOG_FILE = LOG_DIR / "arena.log"


def setup_logger(name: str = "ai_arena", level: int = logging.DEBUG) -> logging.Logger:
    """
    创建并配置 logger。

    Args:
        name: logger 名称
        level: 日志级别

    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 确保日志目录存在
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 文件 handler（详细日志）
    file_handler = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    # 控制台 handler（只显示 INFO 及以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_game_summary(logger: logging.Logger, game_state: dict):
    """
    游戏结束后记录完整游戏日志。

    Args:
        logger: logger 实例
        game_state: 游戏状态快照（来自 game_engine.get_state()）
    """
    logger.info("=" * 60)
    logger.info("🎮 游戏结束 — 完整日志快照")
    logger.info("=" * 60)

    scenario = game_state.get("scenario", {})
    logger.info(f"场景: {scenario.get('emoji', '')} {scenario.get('id', '未知')}")

    players = game_state.get("players", [])
    logger.info(f"玩家数: {len(players)}")
    for p in players:
        status = "存活" if p.get("is_alive") else "淘汰"
        logger.info(f"  {p.get('emoji', '')} {p.get('name', '?')} | 角色: {p.get('role', '?')} | 状态: {status} | 模型: {p.get('model_name', '?')}")

    history = game_state.get("history", [])
    logger.info(f"事件总数: {len(history)}")
    for i, event in enumerate(history):
        etype = event.get("type", "?")
        content = event.get("content", "")[:120]
        pname = event.get("player_name", "")
        prefix = f"[{pname}] " if pname else ""
        logger.info(f"  [{i+1:03d}] {etype:15s} | {prefix}{content}")

    logger.info("=" * 60)


# 全局 logger 实例
arena_logger = setup_logger("ai_arena")
