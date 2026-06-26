"""AI Arena - 游戏主引擎

驱动游戏流程，支持并发 AI 调用、事件回调、状态管理。
"""

import asyncio
import json
from typing import Optional
from .scenarios.base import BaseScenario, Player, GameEvent, GamePhase, PhaseResult
from .ai_client import ai_client, ModelConfig, ChatMessage
from .logger import arena_logger, log_game_summary


class GameEngine:
    """游戏引擎 - 驱动游戏流程

    特性：
    - 事件回调（WebSocket 推送）
    - 并发 AI 调用支持（当多个玩家需要同时行动时）
    - 状态查询
    """

    def __init__(self):
        self.scenario: Optional[BaseScenario] = None
        self.players: list[Player] = []
        self.history: list[GameEvent] = []
        self.current_phase: Optional[GamePhase] = None
        self.is_running: bool = False
        self.model_configs: dict[str, ModelConfig] = {}  # model_name -> ModelConfig
        self._event_callbacks: list = []

    def register_callback(self, callback):
        """注册事件回调（用于 WebSocket 推送）"""
        self._event_callbacks.append(callback)

    def unregister_callback(self, callback):
        """取消注册事件回调"""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    async def _emit_events(self, events: list[GameEvent]):
        """发送事件到所有回调"""
        for event in events:
            self.history.append(event)
            for callback in self._event_callbacks:
                try:
                    await callback(event)
                except Exception:
                    pass

    async def start_game(
        self,
        scenario: BaseScenario,
        players: list[Player],
        model_configs: dict[str, ModelConfig],
    ):
        """开始游戏"""
        self.scenario = scenario
        self.players = players
        self.model_configs = model_configs
        self.history = []
        self.is_running = True

        arena_logger.info(f"游戏开始: {scenario.name}，玩家: {[p.name for p in players]}")

        # 初始化
        setup_events = await scenario.setup(players)
        await self._emit_events(setup_events)

        # 开始第一个阶段
        self.current_phase = GamePhase.NIGHT
        await self._run_game_loop()

    async def _run_game_loop(self):
        """游戏主循环"""
        while self.is_running and self.scenario:
            # 检查胜负
            winner = await self.scenario.check_win_condition(self.players)
            if winner:
                game_over_event = GameEvent(
                    type="game_over",
                    content=f"🎉 游戏结束！{winner}获胜！",
                    data={"winner": winner},
                )
                await self._emit_events([game_over_event])
                arena_logger.info(f"游戏结束: {winner} 获胜")
                self.is_running = False
                break

            arena_logger.debug(f"执行阶段: {self.current_phase}")

            # 执行当前阶段
            result = await self.scenario.run_phase(
                self.current_phase,
                self.players,
                self.history,
                model_configs=self.model_configs,
            )

            # 推送事件
            await self._emit_events(result.events)

            # 切换到下一阶段
            if result.game_over:
                arena_logger.info(f"游戏结束 (game_over=True)")
                self.is_running = False
                break

            if result.next_phase:
                self.current_phase = result.next_phase
            else:
                # 默认循环
                if self.current_phase == GamePhase.NIGHT:
                    self.current_phase = GamePhase.DAY_DISCUSSION
                elif self.current_phase == GamePhase.DAY_DISCUSSION:
                    self.current_phase = GamePhase.DAY_VOTE
                elif self.current_phase == GamePhase.DAY_VOTE:
                    self.current_phase = GamePhase.NIGHT

            # 暂停一下，让前端有时间渲染
            await asyncio.sleep(1)

    async def run_concurrent_ai_calls(
        self,
        tasks: list[tuple],
    ) -> list:
        """
        并发执行多个 AI 调用任务。

        用于多个玩家需要同时行动的场景（如知识问答抢答、代码对决等）。

        Args:
            tasks: [(player, prompt, system_prompt, kwargs), ...] 的列表

        Returns:
            与 tasks 对应的结果列表
        """
        async def _run_one(player, prompt, system_prompt, kwargs):
            model = self._get_model_config(player)
            if not model:
                return None
            try:
                return await ai_client.chat(
                    model=model,
                    system_prompt=system_prompt,
                    messages=[ChatMessage(role="user", content=prompt)],
                    **kwargs,
                )
            except Exception as e:
                arena_logger.warning(f"并发 AI 调用失败 ({player.name}): {e}")
                return None

        coros = [_run_one(p, prompt, sp, kw) for p, prompt, sp, kw in tasks]
        return await asyncio.gather(*coros, return_exceptions=True)

    def _get_model_config(self, player: Player) -> Optional[ModelConfig]:
        """获取玩家对应的模型配置"""
        return self.model_configs.get(player.model_name)

    async def stop_game(self):
        """停止游戏"""
        if self.is_running:
            arena_logger.info("游戏被停止")
        self.is_running = False
        self.current_phase = None

    async def reset_game(self):
        """重置游戏"""
        await self.stop_game()
        self.players = []
        self.history = []
        self.scenario = None
        arena_logger.info("游戏已重置")

    def get_state(self) -> dict:
        """获取游戏状态"""
        return {
            "is_running": self.is_running,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "model_name": p.model_name,
                    "emoji": p.emoji,
                    "color": p.color,
                    "role": p.role,
                    "personality": p.personality,
                    "is_alive": p.is_alive,
                }
                for p in self.players
            ],
            "history": [
                {
                    "type": e.type,
                    "player_id": e.player_id,
                    "player_name": e.player_name,
                    "player_emoji": e.player_emoji,
                    "player_color": e.player_color,
                    "content": e.content,
                    "phase": e.phase,
                }
                for e in self.history
            ],
            "scenario": {
                "id": self.scenario.name if self.scenario else None,
                "emoji": self.scenario.emoji if self.scenario else None,
            },
        }


# 全局游戏引擎实例
game_engine = GameEngine()
