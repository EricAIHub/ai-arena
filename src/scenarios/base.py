"""AI Arena - 场景基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..ai_client import ModelConfig


class GamePhase(str, Enum):
    """游戏阶段"""
    SETUP = "setup"
    NIGHT = "night"
    DAY_DISCUSSION = "day_discussion"
    DAY_VOTE = "day_vote"
    RESULT = "result"
    GAME_OVER = "game_over"


@dataclass
class Player:
    """玩家"""
    id: str
    name: str
    model_name: str           # 对应 config 中的 model name
    emoji: str = "🤖"
    color: str = "#666666"
    role: Optional[str] = None
    personality: str = ""
    is_alive: bool = True
    extra: dict = field(default_factory=dict)  # 场景自定义数据


@dataclass
class GameEvent:
    """游戏事件（用于实时推送到前端）"""
    type: str                 # "speech" | "vote" | "death" | "phase_change" | "system" | "game_over"
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    player_emoji: Optional[str] = None
    player_color: Optional[str] = None
    content: str = ""
    phase: Optional[str] = None
    data: Optional[dict] = None


@dataclass
class PhaseResult:
    """阶段执行结果"""
    events: list[GameEvent]
    next_phase: Optional[GamePhase] = None
    game_over: bool = False
    winner: Optional[str] = None


class BaseScenario(ABC):
    """场景基类 - 所有场景必须继承此类"""

    name: str = "未命名场景"
    description: str = ""
    min_players: int = 2
    max_players: int = 10
    emoji: str = "🎮"

    @abstractmethod
    async def setup(self, players: list[Player]) -> list[GameEvent]:
        """
        初始化游戏（分配角色、宣布规则等）。

        Args:
            players: 玩家列表

        Returns:
            初始化阶段的事件列表
        """
        ...

    @abstractmethod
    async def run_phase(
        self,
        phase: GamePhase,
        players: list[Player],
        history: list[GameEvent],
        model_configs: Optional[dict] = None,
    ) -> PhaseResult:
        """
        执行一个游戏阶段。

        Args:
            phase: 当前阶段
            players: 玩家列表
            history: 之前的事件历史
            model_configs: model_name -> ModelConfig 映射

        Returns:
            阶段执行结果
        """
        ...

    @abstractmethod
    async def get_ai_prompt(
        self,
        player: Player,
        phase: GamePhase,
        history: list[GameEvent],
    ) -> str:
        """
        为某个 AI 生成当前阶段的 prompt。

        Args:
            player: 目标玩家
            phase: 当前阶段
            history: 事件历史

        Returns:
            完整的 prompt 文本
        """
        ...

    @abstractmethod
    async def check_win_condition(self, players: list[Player]) -> Optional[str]:
        """
        检查胜负条件。

        Args:
            players: 玩家列表

        Returns:
            赢家描述（如 "好人阵营"），或 None 表示游戏继续
        """
        ...

    def get_visible_info(self, player: Player, history: list[GameEvent]) -> list[GameEvent]:
        """
        获取某个玩家可见的事件（默认全部可见，子类可覆盖实现信息隐藏）。

        Args:
            player: 目标玩家
            history: 全部事件历史

        Returns:
            该玩家可见的事件列表
        """
        return history

    def _get_model_config(self, player: Player) -> Optional["ModelConfig"]:
        """从 model_configs 中获取玩家对应的模型配置"""
        if not hasattr(self, '_model_configs') or not self._model_configs:
            return None
        return self._model_configs.get(player.model_name)
