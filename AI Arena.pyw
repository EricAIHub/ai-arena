import webview
import threading
import subprocess
import sys
import os
import time
from pathlib import Path

P = Path(os.getcwd())
srv = None

def start_server():
    global srv
    srv = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(P),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=0x08000000 if sys.platform == "win32" else 0,
    )

def wait_for_server():
    import httpx
    for _ in range(30):
        try:
            r = httpx.get("http://127.0.0.1:8000/", timeout=1)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

if __name__ == "__main__":
    # 启动后端
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    # 等待后端就绪
    wait_for_server()

    # 创建桌面窗口
    window = webview.create_window(
        title="AI Arena",
        url="http://127.0.0.1:8000",
        width=1200,
        height=800,
        min_size=(900, 600),
        background_color="#0a0a0f",
    )

    # 启动（关闭窗口时自动退出）
    webview.start()

    # 清理
    if srv:
        srv.terminate()
