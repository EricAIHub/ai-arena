"""API endpoint tests"""
import sys
sys.path.insert(0, ".")

from src.main import app


def test_routes():
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    required = [
        "/", "/api/config", "/api/scenarios",
        "/api/game/start", "/api/game/stop", "/api/game/state",
        "/api/leaderboard", "/api/chronicle",
    ]
    for r in required:
        assert r in routes, f"Missing route: {r}"
    print("  routes: OK")


def test_app_meta():
    assert app.title == "AI Arena"
    print("  app_meta: OK")


if __name__ == "__main__":
    test_routes()
    test_app_meta()
    print("All API tests passed")
