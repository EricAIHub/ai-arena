"""AI Arena - 后端 API 测试脚本"""

import asyncio
import json
import sys

# 添加项目根目录到 path
sys.path.insert(0, ".")


async def test_api():
    """测试所有 API 端点"""
    try:
        import httpx
    except ImportError:
        print("❌ 需要安装 httpx: pip install httpx")
        return

    base_url = "http://127.0.0.1:8077"
    results = []

    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        # 测试 1: GET / 返回 HTML
        print("\n[测试 1] GET / → 主页面")
        try:
            resp = await client.get("/")
            assert resp.status_code == 200, f"状态码: {resp.status_code}"
            assert "text/html" in resp.headers.get("content-type", ""), "不是 HTML"
            assert len(resp.text) > 100, "HTML 内容太短"
            print(f"  ✅ 返回 HTML ({len(resp.text)} 字符)")
            results.append(("GET /", True))
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            results.append(("GET /", False))

        # 测试 2: GET /api/scenarios 返回中文场景列表
        print("\n[测试 2] GET /api/scenarios → 场景列表")
        try:
            resp = await client.get("/api/scenarios")
            assert resp.status_code == 200, f"状态码: {resp.status_code}"
            data = resp.json()
            scenarios = data.get("scenarios", [])
            assert len(scenarios) > 0, "场景列表为空"
            # 检查中文
            first = scenarios[0]
            assert "name" in first, "缺少 name 字段"
            assert "狼" in first["name"] or "辩" in first["name"], f"中文可能乱码: {first['name']}"
            print(f"  ✅ 返回 {len(scenarios)} 个场景: {[s['name'] for s in scenarios]}")
            # 检查 content-type 包含 utf-8
            ct = resp.headers.get("content-type", "")
            print(f"  📋 Content-Type: {ct}")
            results.append(("GET /api/scenarios", True))
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            results.append(("GET /api/scenarios", False))

        # 测试 3: GET /api/config
        print("\n[测试 3] GET /api/config → 配置")
        try:
            resp = await client.get("/api/config")
            assert resp.status_code == 200, f"状态码: {resp.status_code}"
            data = resp.json()
            assert "models" in data, "缺少 models 字段"
            print(f"  ✅ 返回配置，{len(data['models'])} 个模型")
            results.append(("GET /api/config", True))
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            results.append(("GET /api/config", False))

        # 测试 4: GET /api/game/state
        print("\n[测试 4] GET /api/game/state → 游戏状态")
        try:
            resp = await client.get("/api/game/state")
            assert resp.status_code == 200, f"状态码: {resp.status_code}"
            data = resp.json()
            assert "is_running" in data, "缺少 is_running 字段"
            print(f"  ✅ 游戏运行中: {data['is_running']}")
            results.append(("GET /api/game/state", True))
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            results.append(("GET /api/game/state", False))

    # 测试 5: WebSocket
    print("\n[测试 5] WebSocket /ws/game")
    try:
        import websockets
        async with websockets.connect("ws://127.0.0.1:8077/ws/game") as ws:
            await ws.send("ping")
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            assert resp == "pong", f"期望 pong，收到: {resp}"
            print(f"  ✅ WebSocket ping/pong 正常")
            results.append(("WebSocket /ws/game", True))
    except ImportError:
        print("  ⚠️ 需要安装 websockets: pip install websockets")
        results.append(("WebSocket /ws/game", None))
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        results.append(("WebSocket /ws/game", False))

    # 汇总
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    passed = sum(1 for _, ok in results if ok is True)
    failed = sum(1 for _, ok in results if ok is False)
    skipped = sum(1 for _, ok in results if ok is None)
    for name, ok in results:
        status = "✅" if ok else ("⚠️" if ok is None else "❌")
        print(f"  {status} {name}")
    print(f"\n总计: {passed} 通过 / {failed} 失败 / {skipped} 跳过")

    if failed == 0:
        print("\n🎉 所有测试通过！后端 API 工作正常。")
    else:
        print("\n⚠️ 有测试失败，请检查后端服务。")


if __name__ == "__main__":
    asyncio.run(test_api())
