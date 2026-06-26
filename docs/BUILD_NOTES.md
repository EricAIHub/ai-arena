# AI Arena 构建说明

## 概述

AI Arena 采用 **PyInstaller + electron-builder** 两阶段打包方案：

1. **PyInstaller** 将 Python FastAPI 后端打包为独立可执行文件
2. **electron-builder** 将 Electron 桌面壳 + Python 后端打包为 Windows 安装包 (.exe)

## 架构

```
┌─────────────────────────────────────┐
│         Electron 桌面壳              │
│  electron/main.js                   │
│  ┌───────────────────────────────┐  │
│  │     Chromium 浏览器窗口       │  │
│  │   加载 http://127.0.0.1:8077  │  │
│  └───────────────────────────────┘  │
│           │ 启动                     │
│           ▼                         │
│  ┌───────────────────────────────┐  │
│  │  AI Arena Server.exe          │  │
│  │  (PyInstaller 打包的 Python)   │  │
│  │  FastAPI + uvicorn :8077      │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## 前置条件

- Python 3.10+
- Node.js 18+
- npm

## 一键打包

```batch
build.bat
```

## 手动分步打包

### 1. 安装依赖

```batch
pip install -r requirements.txt
pip install pyinstaller
npm install
npm install -g electron-builder
```

### 2. 生成应用图标（可选）

```batch
python generate_icon.py
```

### 3. 打包 Python 后端

```batch
pyinstaller ai-arena.spec --distpath dist --workpath build --clean -y
```

输出目录：`dist/AI Arena Server/`

### 4. 打包 Electron 安装包

```batch
npm run build:app
```

输出目录：`release/`

## 文件说明

| 文件 | 用途 |
|------|------|
| `ai-arena.spec` | PyInstaller 打包配置 |
| `src/__main__.py` | PyInstaller 入口文件 |
| `generate_icon.py` | 应用图标生成脚本 |
| `build.bat` | 一键打包脚本 |
| `package.json` | Electron + electron-builder 配置 |
| `electron/main.js` | Electron 主进程（支持开发/生产双模式） |

## 路径处理

打包后，`src/main.py` 中的 `BASE_DIR` 会自动切换：

- **开发模式**：`Path(__file__).parent.parent`（项目根目录）
- **打包模式**：`Path(sys.executable).parent`（可执行文件所在目录）

## 打包产物

| 产物 | 位置 | 说明 |
|------|------|------|
| Python 后端 | `dist/AI Arena Server/` | FastAPI 服务端独立可执行文件 |
| Windows 安装包 | `release/AI Arena Setup 0.2.0.exe` | NSIS 安装程序 |

## 已知问题

### 端口冲突
如果 8077 端口被占用，后端将无法启动。请关闭占用该端口的程序。

### 首次运行
首次运行时，`data/config.json` 会自动创建默认配置。请确保安装目录有写权限。

### 杀毒软件误报
PyInstaller 打包的 exe 可能被杀毒软件误报。可在打包时添加 `--key` 参数加密，或提交白名单。

## 故障排查

1. **Python 打包失败**：检查 `requirements.txt` 中的依赖是否都已安装
2. **Electron 打包失败**：检查 `node_modules` 是否完整，运行 `npm install` 重新安装
3. **安装后启动黑屏**：检查 8077 端口是否被占用，查看任务管理器结束残留进程
4. **静态文件 404**：检查 `static/` 目录是否存在于安装目录中
