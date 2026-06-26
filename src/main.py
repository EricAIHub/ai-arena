"""AI Arena - 主入口"""

import sys
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .ai_client import ai_client, ModelConfig
from .game_engine import game_engine
from .scenarios import get_scenario, list_scenarios
from .scenarios.base import Player, GameEvent
from .logger import arena_logger, log_game_summary
from .elo import update_ratings_after_game, get_leaderboard, get_model_rating
from .chronicle import generate_chronicle, generate_share_text


# ── 路径处理（兼容 PyInstaller 打包） ────────────────────────
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后：数据文件在 _internal/ 子目录
    BASE_DIR = Path(sys.executable).parent / '_internal'
else:
    # 开发模式：src/main.py 的上两级目录
    BASE_DIR = Path(__file__).parent.parent

# 配置文件路径
CONFIG_PATH = BASE_DIR / "data" / "config.json"
SNAPSHOT_PATH = BASE_DIR / "data" / "game_state.json"


def load_config() -> dict:
    """加载配置"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"models": [], "default_scenario": "werewolf", "language": "zh"}


def save_config(config: dict):
    """保存配置"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def save_snapshot(state: dict):
    """
    保存游戏状态快照到 data/game_state.json。

    Args:
        state: 游戏状态字典（来自 game_engine.get_state()）
    """
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    arena_logger.debug("游戏状态快照已保存")


def load_snapshot() -> dict | None:
    """
    加载游戏状态快照。

    Returns:
        快照字典，或 None（无快照文件）
    """
    if SNAPSHOT_PATH.exists():
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        arena_logger.info(f"WebSocket 连接建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            arena_logger.info(f"WebSocket 连接断开，当前连接数: {len(self.active_connections)}")

    async def broadcast(self, event: GameEvent):
        """广播游戏事件到所有连接"""
        data = {
            "type": event.type,
            "player_id": event.player_id,
            "player_name": event.player_name,
            "player_emoji": event.player_emoji,
            "player_color": event.player_color,
            "content": event.content,
            "phase": event.phase,
        }
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass

    async def send_error(self, error_msg: str, code: str = "UNKNOWN"):
        """发送错误事件到所有 WebSocket 连接"""
        data = {
            "type": "error",
            "content": error_msg,
            "code": code,
        }
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass


ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时注册游戏事件回调
    async def on_game_event(event: GameEvent):
        await ws_manager.broadcast(event)
        # phase_change 时自动保存快照
        if event.type == "phase_change":
            save_snapshot(game_engine.get_state())

    game_engine.register_callback(on_game_event)
    arena_logger.info("AI Arena 启动")
    yield
    # 关闭时清理
    game_engine.unregister_callback(on_game_event)
    # 游戏结束时记录日志
    if game_engine.is_running:
        log_game_summary(arena_logger, game_engine.get_state())
    await game_engine.stop_game()
    arena_logger.info("AI Arena 关闭")


# 创建 FastAPI 应用
app = FastAPI(title="AI Arena", version="0.2.0", lifespan=lifespan)

# CORS 支持（Electron 需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 全局异常处理中间件 ──────────────────────────────────────

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """全局异常处理中间件，捕获未处理的异常并返回标准错误格式"""
    try:
        return await call_next(request)
    except Exception as e:
        arena_logger.error(f"未捕获异常 [{request.method} {request.url}]: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"服务器内部错误: {str(e)}", "code": "INTERNAL_ERROR"},
        )


# 挂载静态文件
# 打包后 static 在 _internal/static/，开发模式在项目根的 static/
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ==================== 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index():
    """主页面"""
    html_path = static_dir / "index.html"
    if not html_path.exists():
        return HTMLResponse(
            content="<h1>AI Arena</h1><p>静态文件未找到，请检查 static/ 目录</p>",
            status_code=404,
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ==================== API 路由 ====================

@app.get("/api/config")
async def get_config():
    """获取配置"""
    try:
        config = load_config()
        return {"models": config.get("models", [])}
    except Exception as e:
        arena_logger.error(f"读取配置失败: {e}")
        return JSONResponse(status_code=500, content={"error": "读取配置失败", "code": "CONFIG_READ_ERROR"})


@app.post("/api/config")
async def update_config(config: dict):
    """保存配置"""
    try:
        save_config(config)
        arena_logger.info("配置已更新")
        return {"status": "ok"}
    except Exception as e:
        arena_logger.error(f"保存配置失败: {e}")
        return JSONResponse(status_code=500, content={"error": "保存配置失败", "code": "CONFIG_SAVE_ERROR"})


@app.post("/api/config/test")
async def test_connection(model_data: dict):
    """测试模型连接"""
    try:
        # 验证必填字段
        errors = _validate_model_data(model_data)
        if errors:
            return JSONResponse(status_code=400, content={"error": "; ".join(errors), "code": "VALIDATION_ERROR"})

        model = ModelConfig(
            name=model_data.get("name", "test"),
            base_url=model_data.get("base_url", ""),
            api_key=model_data.get("api_key", ""),
            model_name=model_data.get("model_name", ""),
        )
        arena_logger.info(f"测试模型连接: {model.name} ({model.base_url})")
        success, message = await ai_client.test_connection(model)
        arena_logger.info(f"连接测试结果: {'成功' if success else '失败'} - {message}")
        return {"success": success, "message": message}
    except Exception as e:
        arena_logger.error(f"连接测试异常: {e}")
        return JSONResponse(status_code=500, content={"error": f"测试失败: {str(e)}", "code": "TEST_ERROR"})


def _validate_model_data(data: dict) -> list[str]:
    """
    验证模型配置数据格式。

    Args:
        data: 模型配置字典

    Returns:
        错误消息列表（空列表表示验证通过）
    """
    errors = []

    base_url = data.get("base_url", "")
    if not base_url:
        errors.append("base_url 不能为空")
    elif not base_url.startswith(("http://", "https://")):
        errors.append("base_url 格式无效，必须以 http:// 或 https:// 开头")

    api_key = data.get("api_key", "")
    if not api_key:
        errors.append("api_key 不能为空")

    model_name = data.get("model_name", "")
    if not model_name:
        errors.append("model_name 不能为空")

    return errors


@app.get("/api/scenarios")
async def get_scenarios():
    """获取场景列表（UTF-8 中文）"""
    return JSONResponse(
        content={"scenarios": list_scenarios()},
        media_type="application/json; charset=utf-8",
    )


@app.post("/api/game/start")
async def start_game(data: dict):
    """开始游戏"""
    try:
        scenario_id = data.get("scenario", "werewolf")
        players_data = data.get("players", [])
        models_data = data.get("models", [])
        blind_mode = data.get("blind_mode", False)

        # 加载配置获取 API key
        config = load_config()
        config_models = {m["name"]: m for m in config.get("models", [])}

        # 构建模型配置（从后端 config 读取完整 api_key，前端传的可能被掩码）
        model_configs = {}
        for m in models_data:
            name = m.get("name", "")
            # 优先从后端 config 获取完整 api_key
            if name in config_models:
                cm = config_models[name]
                model_configs[name] = ModelConfig(
                    name=name,
                    base_url=cm.get("base_url", ""),
                    api_key=cm.get("api_key", ""),
                    model_name=cm.get("model_name", ""),
                    emoji=m.get("emoji", "🤖"),
                    color=m.get("color", "#666666"),
                )
            elif m.get("api_key"):
                # 后备：使用前端传来的 key（可能被掩码）
                model_configs[name] = ModelConfig(
                    name=name,
                    base_url=m.get("base_url", ""),
                    api_key=m.get("api_key", ""),
                    model_name=m.get("model_name", ""),
                    emoji=m.get("emoji", "🤖"),
                    color=m.get("color", "#666666"),
                )

        # 构建玩家列表
        players = []
        for p in players_data:
            players.append(Player(
                id=p.get("id", f"player_{len(players)}"),
                name=p.get("name", f"玩家{len(players)+1}"),
                model_name=p.get("model_name", ""),
                emoji=p.get("emoji", "🤖"),
                color=p.get("color", "#666666"),
                personality=p.get("personality", ""),
            ))

        # 获取场景
        scenario = get_scenario(scenario_id)

        # 验证玩家数量
        if len(players) < scenario.min_players:
            return JSONResponse(
                status_code=400,
                content={"error": f"至少需要 {scenario.min_players} 名玩家", "code": "PLAYER_COUNT_ERROR"},
            )
        if len(players) > scenario.max_players:
            return JSONResponse(
                status_code=400,
                content={"error": f"最多 {scenario.max_players} 名玩家", "code": "PLAYER_COUNT_ERROR"},
            )

        arena_logger.info(f"开始游戏: {scenario_id}，玩家数: {len(players)}，盲测: {blind_mode}")

        # 启动游戏（后台任务，异常时通过 WebSocket 通知）
        async def _run_game():
            try:
                await game_engine.start_game(scenario, players, model_configs, blind_mode=blind_mode)
                # 游戏结束，记录日志
                state = game_engine.get_state()
                log_game_summary(arena_logger, state)

                # 更新 Elo 排名
                winner = state.get("history", [{}])[-1].get("content", "") if state.get("history") else ""
                for e in reversed(state.get("history", [])):
                    if e.get("type") == "game_over":
                        winner = e.get("data", {}).get("winner", "") or e.get("content", "")
                        break
                try:
                    update_ratings_after_game(
                        scenario=scenario_id,
                        players=game_engine.players,
                        winner=winner,
                        events=game_engine.history,
                    )
                except Exception as elo_err:
                    arena_logger.warning(f"Elo 更新失败: {elo_err}")

                # 生成编年史
                try:
                    chronicle = generate_chronicle(
                        scenario=scenario_id,
                        players=game_engine.players,
                        events=game_engine.history,
                        winner=winner,
                    )
                    # 保存到文件
                    chronicle_path = BASE_DIR / "data" / "last_chronicle.txt"
                    chronicle_path.write_text(chronicle, encoding="utf-8")
                    arena_logger.info("编年史已生成")
                except Exception as ch_err:
                    arena_logger.warning(f"编年史生成失败: {ch_err}")
            except Exception as e:
                arena_logger.error(f"游戏异常终止: {e}", exc_info=True)
                await ws_manager.send_error(f"游戏异常终止：{str(e)}", "GAME_ERROR")
                await ws_manager.broadcast(GameEvent(
                    type="system",
                    content=f"❌ 游戏异常终止：{str(e)}",
                ))

        asyncio.create_task(_run_game())

        return {"status": "started", "scenario": scenario_id}
    except Exception as e:
        arena_logger.error(f"启动游戏失败: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": f"启动失败: {str(e)}", "code": "START_ERROR"})


@app.post("/api/game/stop")
async def stop_game():
    """停止游戏"""
    try:
        await game_engine.stop_game()
        arena_logger.info("游戏已停止")
        return {"status": "stopped"}
    except Exception as e:
        arena_logger.error(f"停止游戏失败: {e}")
        return JSONResponse(status_code=500, content={"error": f"停止失败: {str(e)}", "code": "STOP_ERROR"})


@app.post("/api/game/reset")
async def reset_game():
    """重置游戏"""
    try:
        await game_engine.reset_game()
        arena_logger.info("游戏已重置")
        return {"status": "reset"}
    except Exception as e:
        arena_logger.error(f"重置游戏失败: {e}")
        return JSONResponse(status_code=500, content={"error": f"重置失败: {str(e)}", "code": "RESET_ERROR"})


@app.get("/api/game/state")
async def get_game_state():
    """获取游戏状态"""
    try:
        return game_engine.get_state()
    except Exception as e:
        arena_logger.error(f"获取状态失败: {e}")
        return JSONResponse(status_code=500, content={"error": f"获取状态失败: {str(e)}", "code": "STATE_ERROR"})


@app.get("/api/leaderboard")
async def get_leaderboard_api(scenario: str = "overall", limit: int = 20):
    """获取模型 Elo 排行榜"""
    try:
        from .elo import get_leaderboard
        return {"leaderboard": get_leaderboard(scenario=scenario, limit=limit)}
    except Exception as e:
        arena_logger.error(f"获取排行榜失败: {e}")
        return JSONResponse(status_code=500, content={"error": str(e), "code": "LEADERBOARD_ERROR"})


@app.get("/api/rating/{model_name}")
async def get_model_rating_api(model_name: str, scenario: str = "overall"):
    """获取单个模型的 Elo 评分"""
    try:
        from .elo import get_model_rating
        return get_model_rating(model_name, scenario)
    except Exception as e:
        arena_logger.error(f"获取评分失败: {e}")
        return JSONResponse(status_code=500, content={"error": str(e), "code": "RATING_ERROR"})


@app.get("/api/chronicle")
async def get_chronicle():
    """获取上一局的游戏编年史"""
    try:
        chronicle_path = BASE_DIR / "data" / "last_chronicle.txt"
        if not chronicle_path.exists():
            return JSONResponse(status_code=404, content={"error": "暂无编年史", "code": "NO_CHRONICLE"})
        return {"chronicle": chronicle_path.read_text(encoding="utf-8")}
    except Exception as e:
        arena_logger.error(f"获取编年史失败: {e}")
        return JSONResponse(status_code=500, content={"error": str(e), "code": "CHRONICLE_ERROR"})


@app.get("/api/game/snapshot")
async def get_game_snapshot():
    """
    获取当前游戏状态快照。

    Returns:
        最近一次 phase_change 时保存的游戏状态快照
    """
    try:
        snapshot = load_snapshot()
        if snapshot is None:
            return JSONResponse(status_code=404, content={"error": "暂无快照", "code": "NO_SNAPSHOT"})
        return snapshot
    except Exception as e:
        arena_logger.error(f"读取快照失败: {e}")
        return JSONResponse(status_code=500, content={"error": f"读取快照失败: {str(e)}", "code": "SNAPSHOT_ERROR"})


@app.post("/api/game/restore")
async def restore_game_snapshot():
    """
    从快照恢复游戏状态。

    注意：恢复操作会重置当前游戏，并将快照中的玩家状态恢复。
    完整的游戏流程恢复需要前端配合重新开始。
    """
    try:
        snapshot = load_snapshot()
        if snapshot is None:
            return JSONResponse(status_code=404, content={"error": "暂无快照可恢复", "code": "NO_SNAPSHOT"})

        # 停止当前游戏
        await game_engine.stop_game()

        # 恢复玩家状态
        players_data = snapshot.get("players", [])
        restored_players = []
        for p in players_data:
            player = Player(
                id=p.get("id", ""),
                name=p.get("name", ""),
                model_name=p.get("model_name", ""),
                emoji=p.get("emoji", "🤖"),
                color=p.get("color", "#666666"),
                role=p.get("role"),
                personality=p.get("personality", ""),
                is_alive=p.get("is_alive", True),
            )
            restored_players.append(player)

        # 恢复历史事件
        history_data = snapshot.get("history", [])
        restored_history = []
        for e in history_data:
            restored_history.append(GameEvent(
                type=e.get("type", "system"),
                player_id=e.get("player_id"),
                player_name=e.get("player_name"),
                player_emoji=e.get("player_emoji"),
                player_color=e.get("player_color"),
                content=e.get("content", ""),
                phase=e.get("phase"),
            ))

        # 更新游戏引擎状态
        game_engine.players = restored_players
        game_engine.history = restored_history

        phase_str = snapshot.get("current_phase")
        if phase_str:
            from .scenarios.base import GamePhase
            try:
                game_engine.current_phase = GamePhase(phase_str)
            except ValueError:
                game_engine.current_phase = None

        arena_logger.info(f"游戏状态已从快照恢复，玩家数: {len(restored_players)}")

        return {
            "status": "restored",
            "players": len(restored_players),
            "history_events": len(restored_history),
        }
    except Exception as e:
        arena_logger.error(f"恢复快照失败: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": f"恢复失败: {str(e)}", "code": "RESTORE_ERROR"})


# ==================== WebSocket ====================

@app.websocket("/ws/game")
async def websocket_game(websocket: WebSocket):
    """游戏 WebSocket 连接"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # 保持连接，接收客户端消息（如心跳）
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        arena_logger.warning(f"WebSocket 异常: {e}")
        try:
            await websocket.send_json({"type": "error", "content": f"连接异常: {str(e)}", "code": "WS_ERROR"})
        except Exception:
            pass
        ws_manager.disconnect(websocket)


# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8077)
