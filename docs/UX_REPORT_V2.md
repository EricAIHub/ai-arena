# AI Arena — 第二轮深度体验报告

**体验官**: 产品体验官 v2  
**日期**: 2026-06-26  
**版本**: 0.1.0  
**工作目录**: `ai-arena/`

---

## 📋 总览

| 维度 | 评分 | 说明 |
|------|------|------|
| 整体体验 | 7.5/10 | 框架完整，视觉出色，有数个关键 bug |
| 视觉设计 | 9/10 | 玻璃拟态 + 渐变光效非常漂亮 |
| 功能完整性 | 7/10 | 核心流程跑通，细节有缺失 |
| 稳定性 | 6/10 | 有数个会导致功能失效的 bug |
| 代码质量 | 8/10 | 结构清晰，模块化良好 |

---

## 🔴 严重问题（P0 — 必须修复）

### BUG-01: 辩论赛场景 `personality_text` 调用错误
- **文件**: `src/scenarios/debate.py` → `get_ai_prompt()`
- **位置**: 第 ~130 行
- **问题**: 调用了 `personality_text(player)` 函数，但该函数在文件底部定义。虽然 Python 会在运行时解析，**更大的问题是**：辩论赛使用 `PhaseResult` 返回值时，`run_phase` 方法中 `day_discussion` 阶段的 `next_phase` 逻辑有缺陷 —— 当 `debate_round < max_rounds` 时返回 `next_phase=GamePhase.DAY_DISCUSSION`，这会导致 `_run_game_loop` 中的默认阶段切换逻辑被跳过（因为 `result.next_phase` 非空）。实际上这是**正确的**，因为辩论赛确实要循环讨论阶段。但需要确认 `_run_game_loop` 中 `check_win_condition` 在辩论赛场景下的行为：`check_win_condition` 只在 `self.game_over` 为 True 时返回非 None，而 `game_over` 只在 RESULT 阶段才被设为 True。这意味着在 `DAY_DISCUSSION` 循环期间，`check_win_condition` 会在每轮讨论前被调用并返回 None，游戏引擎会继续执行 —— **这是正确的行为**。降级为非 bug。
- **严重性**: ~~P0~~ → 已确认无 bug

### BUG-02: `get_config` 掩码 API Key 导致前端保存时丢失原始 Key 🔴
- **文件**: `src/main.py` → `GET /api/config`
- **问题**: 
  1. `GET /api/config` 返回掩码后的 API Key（如 `sk-a****xyz`）
  2. 前端 `ConfigPanel.loadModels()` 直接将掩码后的值存入 `this.models`
  3. 用户点击"保存"或修改其他字段时，`POST /api/config` 会把掩码后的 Key 写回文件
  4. **原始 API Key 被永久覆盖为掩码值，模型将无法连接**
- **影响**: 用户第一次保存配置后，所有 API Key 将失效
- **修复建议**: 
  - 方案 A（推荐）: 前端保存时，对未修改的 Key（仍含 `****`）跳过覆盖，后端保留原始值
  - 方案 B: 后端提供单独的 `/api/config/models` 端点用于保存模型列表，保留原始 Key
  - 方案 C: 前端不回显 Key，只显示"已设置"标记，保存时只更新用户实际修改的字段

### BUG-03: `game_engine._run_game_loop` 在所有场景中调用 `check_win_condition` 时机不当 🔴
- **文件**: `src/game_engine.py`
- **问题**: 游戏循环在每个阶段开始前检查胜负。对于狼人杀这是正确的，但对于辩论赛/知识问答/代码对决/故事接龙，这些场景的胜负由裁判在 RESULT 阶段判定。`check_win_condition` 在这些场景中只在 `game_over=True` 时返回非 None，而 `game_over` 只在 RESULT 阶段结束后才设为 True。
  
  **实际影响**：当辩论赛 `run_phase` 返回 `game_over=True` 时，游戏循环会先执行 `_emit_events`，然后检查 `result.game_over` 为 True，设置 `self.is_running = False` 并 break。**但在此之前**，循环顶部的 `check_win_condition` 会在下一轮迭代中被调用 —— 不对，仔细看代码：`result.game_over` 检查在 `_emit_events` 之后、阶段切换之前。如果 `result.game_over` 为 True，直接 break，不会再调用 `check_win_condition`。**这是正确的**。
  
  但有一个真实问题：`check_win_condition` 返回非 None 时，会发射一个 `game_over` 事件，但**不会发射 `result.game_over=True` 时对应的事件**。对于狼人杀，当最后一名狼人被投票淘汰后，下一循环的 `check_win_condition` 返回"好人阵营"，此时游戏引擎发射一个 game_over 事件。但狼人杀的 `_run_vote` 中被淘汰事件已发射，然后 `check_win_condition` 在下一轮循环顶部被调用。**这意味着狼人杀的 game_over 事件是由游戏引擎发出的，而不是场景发出的**，格式为 `"🎉 游戏结束！{winner}获胜！"`。而其他场景的 game_over 事件由场景自己发出。格式不一致但功能正确。

- **严重性**: 降级为非 bug，但建议统一 game_over 事件的发出方

### BUG-04: 前端 `scenario-card` 的 `data-scenario` 属性值与 CSS 选择器不匹配 🔴
- **文件**: `static/js/components/scenario-select.js` → `createScenarioCard()`
- **问题**: 
  - JS 中设置 `data-scenario-id="${scenario.id}"`（注意是 `data-scenario-id`）
  - CSS `layout.css` 中的选择器是 `.scenario-card[data-scenario="werewolf"]`（注意是 `data-scenario`，不带 `-id`）
  - **结果**: 场景卡片的主题色（彩色顶条）不会生效，所有场景卡片使用默认的紫色
- **影响**: 场景卡片缺少个性化主题色，视觉辨识度降低
- **修复**: JS 中改为 `data-scenario="${scenario.id}"`，或 CSS 选择器改为 `[data-scenario-id="werewolf"]`

### BUG-05: 豪华主题 `theme-deluxe.css` 中场景卡片选择器使用类名而非属性选择器 🔴
- **文件**: `static/css/theme-deluxe.css`
- **问题**: 
  - CSS 使用 `.scenario-card-werewolf::before` 等类名选择器
  - 但 JS 中从未给场景卡片添加 `scenario-card-werewolf` 等类名
  - JS 只设置了 `data-scenario-id` 属性
  - **结果**: 豪华主题下的彩色顶条完全不生效
- **影响**: 豪华主题的核心特色功能失效
- **修复**: 统一使用属性选择器，如 `.scenario-card[data-scenario="werewolf"]::before`

### BUG-06: `config-panel.js` 保存配置时不保留原始 API Key 🔴
- **文件**: `static/js/components/config-panel.js` → `saveModels()`
- **问题**: 与 BUG-02 联动。`saveModels()` 直接 `await API.saveConfig({ models: this.models })`，但 `this.models` 中的 `api_key` 已经是掩码后的值。
- **影响**: 每次自动保存（输入框 change 事件）都会把掩码 Key 写回后端
- **修复**: 需要前后端配合解决（见 BUG-02 修复建议）

---

## 🟡 中等问题（P1 — 应该修复）

### UX-01: 配置页预设模板菜单定位问题
- **文件**: `static/js/components/config-panel.js` → `showPresetMenu()`
- **问题**: 预设菜单使用 `position: absolute` 但没有设置父容器为 `position: relative`。菜单的定位依赖于 `addBtn.parentNode.insertBefore(menu, addBtn.nextSibling)`，在"添加模型"按钮下方插入。但如果页面有滚动，菜单位置可能不准确。
- **影响**: 在某些情况下菜单可能错位
- **修复**: 菜单使用 `position: fixed` 并根据按钮位置动态计算坐标

### UX-02: 新手引导没有跳过配置直接去场景的快捷方式
- **文件**: `static/index.html` + `static/js/app.js`
- **问题**: 引导卡片第②步说"切换到「场景」标签"，但没有提供直接跳转的链接按钮
- **影响**: 用户需要手动点击导航栏
- **修复**: 在引导步骤中添加可点击的跳转链接

### UX-03: 观战面板玩家状态栏缺少初始渲染
- **文件**: `static/js/components/arena.js`
- **问题**: `onGameStart()` 只清空了 feed 和更新头部，但没有渲染玩家状态栏。玩家状态只有在收到 `death` 事件时才通过 `updatePlayerStatus` 更新，但**从未初始化渲染玩家卡片**。
- **影响**: 观战面板底部的玩家状态栏始终为空
- **修复**: 在 `onGameStart()` 中接收玩家列表并渲染初始状态栏

### UX-04: WebSocket 断线重连后不会同步游戏状态
- **文件**: `static/js/websocket.js`
- **问题**: WebSocket 断线重连后，只是重新建立连接，不会请求当前游戏状态。如果在游戏进行中断线，重连后会丢失中间的事件。
- **影响**: 断线期间的游戏事件会永久丢失
- **修复**: 重连成功后调用 `API.getGameState()` 同步状态

### UX-05: 暂停按钮功能未实现
- **文件**: `static/index.html` 中有 `btn-pause` 按钮
- **问题**: HTML 中存在暂停按钮，但 `arena.js` 中没有绑定任何事件，`game_engine.py` 中也没有 `pause` 功能
- **影响**: 按钮点击无反应
- **修复**: 要么实现暂停功能，要么移除按钮

### UX-06: 狼人杀场景 `_get_ai_choice` 的正则解析不够健壮
- **文件**: `src/scenarios/werewolf.py` → `_get_ai_choice()`
- **问题**: 正则 `r'[：:]\s*(.+?)(?:\s*$|[。.！!，,])'` 在 AI 回复格式不符合预期时可能匹配错误。例如 AI 回复"我认为应该击杀张三，因为..."会匹配到"张三，因为..."。
- **影响**: 偶尔投票/击杀目标解析错误，fallback 到随机选择
- **修复**: 先匹配候选列表中的名字，再尝试正则提取

### UX-07: `start.bat` 与 `AI Arena.bat` 启动方式不一致
- **文件**: `start.bat` vs `AI Arena.bat`
- **问题**: `AI Arena.bat` 使用 Electron 启动（端口自动选择），`AI Arena.pyw` 使用 pywebview 启动（端口 8000），`electron/main.js` 使用端口 8077。三套启动方式，用户容易混淆。
- **影响**: 用户可能用不同的启动方式导致端口冲突或找不到服务
- **修复**: 统一为一种启动方式，或在 README 中明确说明

### UX-08: 狼人杀场景需要 6 人但前端没有强制验证
- **文件**: `static/js/components/scenario-select.js`
- **问题**: `showPlayerSetup` 中默认创建 `scenario.min_players` 个玩家，但用户可以删除玩家行（虽然当前没有删除按钮）。更关键的是，如果用户只配置了 2 个模型，6 个玩家会循环使用这 2 个模型，导致 AI 行为重复。
- **影响**: 模型不足时游戏体验下降
- **修复**: 当配置的模型数量 < min_players 时，显示提示并建议用户添加更多模型

### UX-09: `judge.py` 中 `judge_debate` / `judge_code_duel` / `judge_storytelling` 未被使用
- **文件**: `src/judge.py`
- **问题**: 裁判系统定义了三个评判方法，但实际的辩论赛/代码对决/故事接龙场景都自己实现了评判逻辑（在各自的场景文件中）。`Judge` 类完全没有被使用。
- **影响**: 代码冗余，维护时容易产生不一致
- **修复**: 统一使用 `judge.py` 中的评判逻辑，或删除 `judge.py`

---

## 🟢 小问题（P2 — 建议修复）

### POLISH-01: Splash 窗口 8 秒超时后不会显示错误信息
- **文件**: `electron/main.js` → `startBackend()`
- **问题**: `setTimeout(resolve, 8000)` 确保即使后端启动失败也会继续。但如果后端确实启动失败，`createWindow()` 会加载一个不存在的 URL，显示空白页面或错误。
- **修复**: `waitForBackend()` 返回 false 时，在 splash 上显示错误信息

### POLISH-02: `electron/main.js` 中 `window-all-closed` 不会关闭 Windows 上的主窗口
- **文件**: `electron/main.js`
- **问题**: `app.on('window-all-closed')` 中先关闭 splash 再 kill python 再 quit。但 `mainWindow` 的 `closed` 事件已经将 `mainWindow = null`，所以 `BrowserWindow.getAllWindows()` 可能不包含已关闭的窗口。在 Windows 上，如果用户关闭主窗口，`window-all-closed` 事件会触发，python 进程会被正确清理。**这是正确的**。
- **降级**: 非问题

### POLISH-03: CSS 变量中 `--accent-*` 使用 RGB 值但需要配合 `rgba()` 使用
- **文件**: `static/css/variables.css`
- **问题**: `--accent-werewolf: 239, 68, 68;` 定义为 RGB 三元组，CSS 中使用时需要 `rgba(var(--accent-werewolf), 0.5)`。这在现代浏览器中可以工作，但 `layout.css` 中使用了 `rgba(var(--scenario-accent, 99, 102, 241), 0.25)`，fallback 值也是三元组格式，**这是正确的**。
- **降级**: 非问题，设计合理

### POLISH-04: `Helpers.createElement` 的 `style` 属性支持对象但 `scenario-select.js` 传入字符串
- **文件**: `static/js/utils/helpers.js` + `static/js/components/scenario-select.js`
- **问题**: `createElement` 检查 `typeof value === 'object'` 来处理 style，但 `scenario-select.js` 中使用 `style: 'display: flex; gap: ...'`（字符串）。`createElement` 会走到 `else` 分支调用 `el.setAttribute('style', ...)`，字符串形式的 style 会被正确设置。**功能正确但不一致**。
- **修复**: 统一使用对象形式或字符串形式

### POLISH-05: 前端没有错误 Toast 提示
- **文件**: 全局
- **问题**: API 调用失败时只 `console.error` 或 `alert()`，没有优雅的 Toast 提示
- **修复**: 实现轻量级 Toast 组件

### POLISH-06: `data/scenarios/*.yaml` 文件未被后端使用
- **文件**: `data/scenarios/` 目录下有 5 个 YAML 文件
- **问题**: 场景配置完全硬编码在 Python 文件中，YAML 文件只是文档性质，没有被加载
- **修复**: 要么从 YAML 动态加载场景配置，要么删除 YAML 文件避免混淆

### POLISH-07: `requirements.txt` 缺少版本锁定
- **文件**: `requirements.txt`
- **问题**: 所有依赖都没有版本号，可能导致不同环境下行为不一致
- **修复**: 添加版本约束，如 `fastapi>=0.100.0`

### POLISH-08: 观战面板 `btn-stop` 没有确认对话框
- **文件**: `static/js/components/arena.js`
- **问题**: 点击"停止"按钮直接停止游戏，没有二次确认
- **修复**: 添加 `confirm()` 确认

### POLISH-09: 狼人杀夜晚阶段只有第一个狼人做选择
- **文件**: `src/scenarios/werewolf.py` → `_run_night()`
- **问题**: `wolves[0]` 做选择，其他狼人没有参与。在多人狼人杀中，狼人应该协商（或各自投票）。
- **修复**: 让所有狼人分别选择，取多数票或第一个有效选择

### POLISH-10: `start.bat` 中 `ELECTRON_MIRROR` 设置可能不生效
- **文件**: `AI Arena.bat`
- **问题**: `set ELECTRON_MIRROR=...` 在 `npm install` 之前设置，但 npm 可能已经缓存了 electron，镜像设置不会生效。且如果 electron 已安装，条件检查会跳过安装。
- **影响**: 首次安装时可能从官方源下载较慢
- **降级**: 小问题

---

## 🧭 用户旅程评分

### 旅程 1: 启动 → Splash → 主界面

| 步骤 | 评分 | 说明 |
|------|------|------|
| 双击启动 | 8/10 | `AI Arena.bat` 启动流程清晰，有安装提示 |
| Splash 显示 | 9/10 | 动画流畅，渐变文字漂亮，3 个弹跳点加载动画 |
| 后端启动 | 7/10 | 8 秒超时合理，但失败时无错误提示 |
| 主界面加载 | 9/10 | 玻璃拟态导航栏 + 渐变光效，视觉出色 |
| **平均** | **8.3/10** | |

### 旅程 2: 首次引导 → 添加模型 → 测试连接

| 步骤 | 评分 | 说明 |
|------|------|------|
| 引导卡片显示 | 8/10 | 自动显示，步骤清晰，有推荐平台链接 |
| 添加模型 | 8/10 | 预设模板菜单方便，5 个选项覆盖主流 |
| 填写 API Key | 7/10 | 有显示/隐藏切换，但掩码 Key 保存 bug 严重 |
| 测试连接 | 8/10 | 按钮状态反馈清晰（⏳→✅/❌），3 秒自动恢复 |
| 保存配置 | 5/10 | **BUG-02 导致 API Key 被掩码覆盖，致命** |
| **平均** | **7.2/10** | 被 API Key bug 严重拉低 |

### 旅程 3: 选择场景 → 配置玩家 → 开始游戏

| 步骤 | 评分 | 说明 |
|------|------|------|
| 场景卡片展示 | 8/10 | 卡片设计精美，有 emoji、描述、人数标签 |
| 主题色顶条 | 3/10 | **BUG-04/05 导致彩色顶条完全不生效** |
| 玩家配置面板 | 7/10 | 自动填充模型名，支持自定义人设 |
| 开始游戏 | 8/10 | 按钮状态反馈好，自动切换到观战页 |
| **平均** | **6.5/10** | 场景卡片主题色缺失影响体验 |

### 旅程 4: 观战 → AI 发言 → 投票 → 淘汰

| 步骤 | 评分 | 说明 |
|------|------|------|
| 观战面板布局 | 9/10 | 三栏布局（头部+事件流+状态栏）合理 |
| AI 发言展示 | 9/10 | 气泡样式精致，头像+名字+内容层次清晰 |
| 系统事件 | 8/10 | 居中显示，左侧渐变条装饰，区分度好 |
| 投票事件 | 8/10 | 琥珀色左边框 + 光效，视觉区分明确 |
| 淘汰事件 | 8/10 | 红色左边框 + 光效，氛围感强 |
| 阶段切换 | 8/10 | 阶段标签清晰，emoji 标识直观 |
| 玩家状态栏 | 3/10 | **UX-03: 状态栏从未初始化渲染，始终为空** |
| 自动滚动 | 9/10 | `scrollToBottom()` 确保新消息可见 |
| **平均** | **7.8/10** | 状态栏 bug 是明显短板 |

### 旅程 5: 游戏结束 → 再来一局

| 步骤 | 评分 | 说明 |
|------|------|------|
| Game Over 展示 | 9/10 | 渐变文字 + 光效边框，庆祝感强 |
| 再来一局按钮 | 8/10 | 存在且可用，自动跳转到场景选择 |
| 状态重置 | 8/10 | `reset()` 方法清理了所有状态 |
| **平均** | **8.3/10** | |

### 旅程 6: 切换主题 → 对比效果

| 步骤 | 评分 | 说明 |
|------|------|------|
| 主题切换按钮 | 8/10 | 导航栏右侧 🌑 按钮，位置合理 |
| 切换动画 | 7/10 | 即时切换，无过渡动画（可接受） |
| 纯净主题 | 9/10 | 默认主题，深色 + 渐变光斑，精致 |
| 豪华主题 | 6/10 | 渐变光斑实现好，但场景彩色顶条失效 |
| 柔和主题 | 8/10 | 暖色点缀实现好，视觉舒适 |
| 主题持久化 | 9/10 | localStorage 保存，刷新后保持 |
| **平均** | **7.8/10** | 豪华主题的 bug 拉低分数 |

### 旅程 7: 关闭应用

| 步骤 | 评分 | 说明 |
|------|------|------|
| 关闭窗口 | 8/10 | Electron 正确清理 python 进程 |
| 进程清理 | 8/10 | `pythonProc.kill()` 确保无残留 |
| **平均** | **8/10** | |

---

## 📊 问题汇总统计

| 严重性 | 数量 | 编号 |
|--------|------|------|
| 🔴 P0 严重 | 4 | BUG-02, BUG-04, BUG-05, BUG-06 |
| 🟡 P1 中等 | 9 | UX-01 ~ UX-09 |
| 🟢 P2 小问题 | 10 | POLISH-01 ~ POLISH-10 |
| **总计** | **23** | |

---

## 🎯 优先级排序（修复顺序）

### 第一批：阻断性 Bug（必须立即修复）
1. **BUG-02 + BUG-06**: API Key 掩码覆盖问题 — 这会导致用户配置永久失效
2. **BUG-04 + BUG-05**: 场景卡片主题色选择器不匹配 — 影响所有场景的视觉辨识

### 第二批：体验关键缺陷
3. **UX-03**: 观战面板玩家状态栏未初始化渲染
4. **UX-06**: 狼人杀 AI 选择解析不够健壮
5. **UX-05**: 暂停按钮功能未实现（移除或实现）

### 第三批：体验优化
6. **UX-01**: 预设菜单定位问题
7. **UX-04**: WebSocket 重连后状态同步
8. **UX-08**: 模型不足时的提示
9. **UX-09**: 清理未使用的 judge.py 代码

### 第四批：打磨
10. **POLISH-01 ~ POLISH-10**: 错误提示、Toast、YAML 清理等

---

## 💡 整体建议

### 亮点 👍
1. **视觉设计一流**: 玻璃拟态 + 渐变光效 + 噪点纹理，比很多商业产品都精致
2. **代码架构清晰**: 前后端分离、场景继承体系、WebSocket 实时推送，工程化程度高
3. **AI 调用统一**: `ai_client.py` 封装了所有 OpenAI 兼容 API，扩展性好
4. **狼人杀场景完整**: 角色分配、夜晚行动、白天讨论、投票淘汰，流程完整
5. **5 个场景覆盖广**: 狼人杀、辩论赛、知识问答、代码对决、故事接龙，类型丰富

### 改进方向 🔧
1. **API Key 安全**: 当前明文存储在 config.json 中，建议加密或使用系统密钥链
2. **错误处理**: 前端缺少统一的错误处理和用户提示机制
3. **状态管理**: 前端使用全局对象（ConfigPanel, ScenarioSelect, Arena）管理状态，建议考虑更结构化的方式
4. **测试覆盖**: 没有看到任何测试文件，建议添加单元测试和集成测试
5. **文档**: README.md 需要更新，包含安装步骤、使用说明、开发指南

---

## 📁 完整性检查

### 文件清单
| 文件 | 状态 | 说明 |
|------|------|------|
| `electron/main.js` | ✅ | 完整 |
| `electron/splash.html` | ✅ | 完整 |
| `static/index.html` | ✅ | 完整 |
| `static/js/app.js` | ✅ | 完整 |
| `static/js/api.js` | ✅ | 完整 |
| `static/js/websocket.js` | ✅ | 完整 |
| `static/js/utils/helpers.js` | ✅ | 完整 |
| `static/js/utils/theme.js` | ✅ | 完整 |
| `static/js/components/config-panel.js` | ✅ | 完整 |
| `static/js/components/scenario-select.js` | ✅ | 完整 |
| `static/js/components/arena.js` | ✅ | 完整 |
| `static/css/variables.css` | ✅ | 完整 |
| `static/css/base.css` | ✅ | 完整 |
| `static/css/components.css` | ✅ | 完整 |
| `static/css/layout.css` | ✅ | 完整 |
| `static/css/animations.css` | ✅ | 完整 |
| `static/css/theme-arena.css` | ✅ | 完整 |
| `static/css/theme-deluxe.css` | ⚠️ | 场景选择器不匹配 |
| `static/css/theme-soft.css` | ✅ | 完整 |
| `src/main.py` | ⚠️ | API Key 掩码 bug |
| `src/ai_client.py` | ✅ | 完整 |
| `src/game_engine.py` | ✅ | 完整 |
| `src/judge.py` | ⚠️ | 未被使用 |
| `src/scenarios/__init__.py` | ✅ | 完整 |
| `src/scenarios/base.py` | ✅ | 完整 |
| `src/scenarios/werewolf.py` | ⚠️ | AI 解析健壮性不足 |
| `src/scenarios/debate.py` | ✅ | 完整 |
| `src/scenarios/quiz.py` | ✅ | 完整 |
| `src/scenarios/code_duel.py` | ✅ | 完整 |
| `src/scenarios/storytelling.py` | ✅ | 完整 |
| `data/config.json` | ✅ | 完整 |
| `data/scenarios/*.yaml` | ⚠️ | 未被使用 |
| `requirements.txt` | ⚠️ | 缺版本号 |
| `package.json` | ✅ | 完整 |

### 未实现的功能
- ❌ 暂停按钮（HTML 存在但未实现）
- ❌ 自定义场景（菜单中有 `custom` 选项但无对应场景）
- ❌ 游戏回放/历史记录

### 前后端数据格式一致性
- ✅ API 端点与前端调用匹配
- ✅ WebSocket 事件格式一致
- ⚠️ `GET /api/config` 返回掩码 Key 与前端保存逻辑冲突

### 安全隐患
- ⚠️ API Key 明文存储在 `data/config.json`
- ⚠️ CORS 设置为 `allow_origins=["*"]`（开发阶段可接受，生产环境需限制）
- ✅ Electron 禁用了 `nodeIntegration`，启用了 `contextIsolation`

---

**报告完毕。** 总体而言，AI Arena 是一个完成度很高的原型，视觉设计出色，核心流程跑通。最紧急的问题是 API Key 掩码导致的配置丢失 bug，修复后产品体验将大幅提升。
