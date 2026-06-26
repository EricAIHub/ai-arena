"""AI Arena - 增强版游戏引擎 v2

在 v1 基础上新增：
- 用户输入等待机制（asyncio.Future）
- 观战/参与模式切换
- 猎人技能触发处理
- 增强的状态管理
"""

import asyncio
import json
from typing import Optional
from .scenarios.base import BaseScenario, Player, GameEvent, GamePhase, PhaseResult
from .ai_client import ai_client, ModelConfig, ChatMessage
from .logger import arena_logger, log_game_summary


class GameEngineV2:
    """增强版游戏引擎

    特性：
    - 事件回调（WebSocket 推送）
    - 并发 AI 调用支持
    - 用户输入等待机制
    - 观战/参与模式切换
    - 增强的状态管理
    """

    def __init__(self):
        self.scenario: Optional[BaseScenario] = None
        self.players: list[Player] = []
        self.history: list[GameEvent] = []
        self.current_phase: Optional[GamePhase] = None
        self.is_running: bool = False
        self.model_configs: dict[str, ModelConfig] = {}
        self._event_callbacks: list = []

        # 用户输入相关
        self._user_input_future: Optional[asyncio.Future] = None
        self._waiting_player_id: Optional[str] = None
        self._input_timeout: float = 120.0  # 默认超时时间

        # 模式管理
        self._human_player_ids: set[str] = set()  # 人类玩家 ID 集合

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

        # 记录人类玩家
        self._human_player_ids = {p.id for p in players if p.is_human}

        arena_logger.info(
            f"游戏开始: {scenario.name}，"
            f"玩家: {[p.name for p in players]}，"
            f"人类玩家: {[p.name for p in players if p.is_human]}"
        )

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
                arena_logger.info("游戏结束 (game_over=True)")
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

    # ── 用户输入机制 ──────────────────────────────────────────

    async def wait_for_user_input(
        self,
        player_id: str,
        prompt: str,
        input_type: str = "speech",
        candidates: Optional[list[dict]] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """等待用户输入

        Args:
            player_id: 等待输入的玩家 ID
            prompt: 提示信息
            input_type: 输入类型 (speech/vote/witch_save/witch_poison/hunter_shoot/guard_protect/seer_check)
            candidates: 可选列表（投票/选择时使用）
            timeout: 超时时间（秒）

        Returns:
            用户输入的内容，超时返回空字符串
        """
        self._user_input_future = asyncio.get_event_loop().create_future()
        self._waiting_player_id = player_id

        # 发送等待事件
        await self._emit_events([GameEvent(
            type="waiting_input",
            player_id=player_id,
            content=prompt,
            data={
                "input_type": input_type,
                "candidates": candidates or [],
                "timeout": timeout or self._input_timeout,
            },
        )])

        arena_logger.info(f"等待用户输入: player_id={player_id}, type={input_type}")

        try:
            # 等待用户输入，带超时
            result = await asyncio.wait_for(
                self._user_input_future,
                timeout=timeout or self._input_timeout,
            )
            arena_logger.info(f"收到用户输入: player_id={player_id}, result={result[:50]}...")
            return result
        except asyncio.TimeoutError:
            arena_logger.warning(f"用户输入超时: player_id={player_id}")
            return ""
        finally:
            self._user_input_future = None
            self._waiting_player_id = None

    async def submit_user_input(self, text: str, choice: Optional[str] = None):
        """用户提交输入

        Args:
            text: 文本内容（发言）
            choice: 选择的目标（投票/技能选择）
        """
        if self._user_input_future and not self._user_input_future.done():
            # 优先使用 choice，其次使用 text
            result = choice or text
            self._user_input_future.set_result(result)
            arena_logger.info(f"用户输入已提交: {result[:50]}...")
        else:
            arena_logger.warning("没有等待中的用户输入")

    def is_waiting_for_input(self) -> bool:
        """是否正在等待用户输入"""
        return self._user_input_future is not None and not self._user_input_future.done()

    def get_waiting_player_id(self) -> Optional[str]:
        """获取正在等待输入的玩家 ID"""
        return self._waiting_player_id

    # ── 模式切换 ──────────────────────────────────────────────

    async def switch_to_spectator(self, player_id: str):
        """切换到观战模式（AI 接管）

        Args:
            player_id: 要切换的玩家 ID
        """
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            arena_logger.warning(f"切换观战模式失败: 找不到玩家 {player_id}")
            return

        if not player.is_human:
            arena_logger.info(f"玩家 {player_id} 已经是 AI 控制")
            return

        player.is_human = False
        self._human_player_ids.discard(player_id)

        # 通知所有客户端
        await self._emit_events([GameEvent(
            type="system",
            content=f"🔄 {player.emoji} {player.name} 已切换到观战模式，AI 接管控制",
        )])

        # 如果正在等待该用户输入，取消等待
        if self._waiting_player_id == player_id and self._user_input_future:
            if not self._user_input_future.done():
                self._user_input_future.set_result("")  # 空输入，让 AI 接管

        arena_logger.info(f"玩家 {player.name} 已切换到观战模式")

    async def switch_to_player(self, player_id: str):
        """切换到参与模式（用户控制）

        Args:
            player_id: 要切换的玩家 ID
        """
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            arena_logger.warning(f"切换参与模式失败: 找不到玩家 {player_id}")
            return

        if player.is_human:
            arena_logger.info(f"玩家 {player_id} 已经是用户控制")
            return

        player.is_human = True
        self._human_player_ids.add(player_id)

        # 通知所有客户端
        await self._emit_events([GameEvent(
            type="system",
            content=f"🎮 {player.emoji} {player.name} 已加入游戏，现在由用户控制",
        )])

        arena_logger.info(f"玩家 {player.name} 已切换到参与模式")

    # ── 并发 AI 调用 ──────────────────────────────────────────

    async def run_concurrent_ai_calls(
        self,
        tasks: list[tuple],
    ) -> list:
        """并发执行多个 AI 调用任务

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

    # ── 游戏控制 ──────────────────────────────────────────────

    async def stop_game(self):
        """停止游戏"""
        if self.is_running:
            arena_logger.info("游戏被停止")
        self.is_running = False
        self.current_phase = None

        # 取消等待中的用户输入
        if self._user_input_future and not self._user_input_future.done():
            self._user_input_future.cancel()

    async def reset_game(self):
        """重置游戏"""
        await self.stop_game()
        self.players = []
        self.history = []
        self.scenario = None
        self._human_player_ids.clear()
        arena_logger.info("游戏已重置")

    def get_state(self) -> dict:
        """获取游戏状态"""
        return {
            "is_running": self.is_running,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "is_waiting_for_input": self.is_waiting_for_input(),
            "waiting_player_id": self.get_waiting_player_id(),
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
                    "is_human": p.is_human,
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
                    "data": e.data,
                }
                for e in self.history
            ],
            "scenario": {
                "id": self.scenario.name if self.scenario else None,
                "emoji": self.scenario.emoji if self.scenario else None,
            },
            "human_player_ids": list(self._human_player_ids),
        }


# 全局游戏引擎实例
game_engine_v2 = GameEngineV2()
