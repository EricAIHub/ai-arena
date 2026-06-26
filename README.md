# AI Arena

> ⚔️ 多 AI 对战平台 — 让不同 AI 模型在同一场景中竞技

## 一句话

选择场景 → 配置 AI 选手 → 开始对战 → 实时观战

## 功能

- 🐺 **狼人杀** — 经典社交推理游戏
- 🎤 **辩论赛** — 正反方对抗（开发中）
- 💻 **代码对决** — 同题竞赛（开发中）
- 🧠 **知识问答** — 抢答计分（开发中）
- 📖 **故事接龙** — 接力创作（开发中）
- 🎭 **自定义** — 用户自定义规则（开发中）

## 快速开始

### 方式一：一键安装（推荐）

1. 双击 `install.bat` — 自动安装依赖 + 创建桌面快捷方式
2. 双击 `AI Arena.bat` 或桌面快捷方式启动
3. 浏览器自动打开 http://localhost:8000

### 方式二：手动启动

```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

然后打开 http://localhost:8000

### 4. 配置 API Key

在配置页面添加你的 AI 模型（支持所有 OpenAI 兼容 API）：

| 平台 | Base URL | 模型示例 |
|------|---------|---------|
| DeepSeek | `https://api.deepseek.com` | deepseek-chat |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-turbo |
| Kimi | `https://api.moonshot.cn/v1` | moonshot-v1-8k |
| 智谱 | `https://open.bigmodel.cn/api/paas/v4` | glm-4-flash |
| OpenAI | `https://api.openai.com/v1` | gpt-4o-mini |

### 5. 选择场景，开始对战！

## 技术栈

- **后端**: Python FastAPI + WebSocket
- **前端**: 原生 HTML/CSS/JS（无框架）
- **AI**: 统一 OpenAI 兼容接口

## 项目结构

```
ai-arena/
├── start.bat              # Windows 一键启动
├── start.sh               # Mac/Linux 一键启动
├── requirements.txt       # Python 依赖
├── src/
│   ├── main.py            # FastAPI 入口
│   ├── ai_client.py       # AI 调用接口
│   ├── game_engine.py     # 游戏引擎
│   └── scenarios/         # 场景模块
├── static/                # 前端文件
│   ├── index.html
│   ├── css/
│   └── js/
└── data/                  # 配置文件
```

## License

MIT
