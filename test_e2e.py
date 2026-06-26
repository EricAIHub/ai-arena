"""AI Arena - 自动化测试脚本"""
import time
from playwright.sync_api import sync_playwright

results = []

def test(name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append((name, passed))
    msg = f"{status}: {name}"
    if detail:
        msg += f" ({detail})"
    print(msg)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    
    # === 1. 页面加载 ===
    print("\n=== 1. 页面加载 ===")
    page.goto("http://127.0.0.1:8077/")
    page.wait_for_load_state("networkidle")
    test("主页加载", True)
    
    # === 2. 导航切换 ===
    print("\n=== 2. 导航切换测试 ===")
    for target in ["scenarios", "arena", "settings", "config"]:
        btn = page.query_selector(f'[data-page="{target}"]')
        if not btn:
            test(f"导航到 {target} - 按钮存在", False, "按钮未找到")
            continue
        btn.click()
        time.sleep(0.6)
        active = page.query_selector(f"#page-{target}.active")
        test(f"导航到 {target}", active is not None)
    
    # === 3. 设置页面 ===
    print("\n=== 3. 设置页面测试 ===")
    page.click('[data-page="settings"]')
    time.sleep(0.5)
    
    test("明暗模式切换器", page.query_selector("#mode-toggle") is not None)
    test("配色方案选择器", page.query_selector("#accent-picker") is not None)
    test("体验模式切换器", page.query_selector("#ux-mode-toggle") is not None)
    
    # 测试明暗切换
    light_btn = page.query_selector('[data-mode="light"]')
    if light_btn:
        light_btn.click()
        time.sleep(0.3)
        mode = page.evaluate('document.documentElement.getAttribute("data-mode")')
        test("切换到明亮模式", mode == "light", f"data-mode={mode}")
    
    dark_btn = page.query_selector('[data-mode="dark"]')
    if dark_btn:
        dark_btn.click()
        time.sleep(0.3)
        mode = page.evaluate('document.documentElement.getAttribute("data-mode")')
        test("切换回暗色模式", mode == "dark", f"data-mode={mode}")
    
    # 测试配色切换
    deluxe_btn = page.query_selector('[data-accent="deluxe"]')
    if deluxe_btn:
        deluxe_btn.click()
        time.sleep(0.3)
        accent = page.evaluate('document.documentElement.getAttribute("data-accent")')
        test("切换到豪华配色", accent == "deluxe", f"data-accent={accent}")
    
    # 测试体验模式
    geek_btn = page.query_selector('[data-ux="geek"]')
    if geek_btn:
        geek_btn.click()
        time.sleep(0.3)
        ux = page.evaluate('document.documentElement.getAttribute("data-ux")')
        test("切换到极客版", ux == "geek", f"data-ux={ux}")
    
    # === 4. 配置页面 ===
    print("\n=== 4. 配置页面测试 ===")
    page.click('[data-page="config"]')
    time.sleep(0.5)
    
    test("模型列表容器", page.query_selector("#model-list") is not None)
    test("添加模型按钮", page.query_selector("#btn-add-model") is not None)
    test("新手引导卡片", page.query_selector("#onboarding-card") is not None)
    
    # 测试添加模型预设菜单
    add_btn = page.query_selector("#btn-add-model")
    if add_btn:
        add_btn.click()
        time.sleep(0.3)
        preset_menu = page.query_selector("#preset-menu")
        test("预设菜单弹出", preset_menu is not None)
    
    # === 5. 场景页面 ===
    print("\n=== 5. 场景页面测试 ===")
    page.click('[data-page="scenarios"]')
    time.sleep(0.5)
    
    scenario_grid = page.query_selector("#scenario-grid")
    test("场景网格容器", scenario_grid is not None)
    
    # 检查场景卡片
    cards = page.query_selector_all(".scenario-card")
    test("场景卡片数量", len(cards) >= 5, f"找到 {len(cards)} 张")
    
    # === 6. 观战页面 ===
    print("\n=== 6. 观战页面测试 ===")
    page.click('[data-page="arena"]')
    time.sleep(0.5)
    
    test("围桌区域", page.query_selector("#arena-table") is not None)
    test("字幕旁白", page.query_selector("#arena-narrator") is not None)
    test("玩家座位区域", page.query_selector("#arena-seats") is not None)
    test("发言区域", page.query_selector("#arena-feed") is not None)
    test("玩家状态栏", page.query_selector("#arena-players") is not None)
    test("暂停按钮", page.query_selector("#btn-pause") is not None)
    test("停止按钮", page.query_selector("#btn-stop") is not None)
    
    # === 7. WebSocket 状态 ===
    print("\n=== 7. WebSocket 连接 ===")
    ws_status = page.query_selector("#ws-status")
    test("WebSocket 状态指示器", ws_status is not None)
    
    # === 8. 主题系统 ===
    print("\n=== 8. 主题系统 ===")
    page.click('[data-page="settings"]')
    time.sleep(0.3)
    
    # 测试暗色+靛蓝
    page.click('[data-mode="dark"]')
    page.click('[data-accent="clean"]')
    time.sleep(0.2)
    mode = page.evaluate('document.documentElement.getAttribute("data-mode")')
    accent = page.evaluate('document.documentElement.getAttribute("data-accent")')
    test("暗色+靛蓝", mode == "dark" and accent == "clean", f"{mode}+{accent}")
    
    # 测试亮色+紫罗兰
    page.click('[data-mode="light"]')
    page.click('[data-accent="deluxe"]')
    time.sleep(0.2)
    mode = page.evaluate('document.documentElement.getAttribute("data-mode")')
    accent = page.evaluate('document.documentElement.getAttribute("data-accent")')
    test("亮色+紫罗兰", mode == "light" and accent == "deluxe", f"{mode}+{accent}")
    
    # === 9. 控制台错误 ===
    print("\n=== 9. JavaScript 错误 ===")
    js_errors = [e for e in errors if "favicon" not in e.lower()]
    test("无 JS 错误", len(js_errors) == 0, f"{len(js_errors)} 个错误")
    if js_errors:
        for e in js_errors[:5]:
            print(f"  ⚠️ {e[:120]}")
    
    browser.close()

# === 汇总 ===
print("\n" + "=" * 50)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total = len(results)
print(f"测试结果: {passed}/{total} 通过, {failed} 失败")
if failed == 0:
    print("🎉 全部通过！")
else:
    print("⚠️ 有失败项，需要修复")
    for name, ok in results:
        if not ok:
            print(f"  ❌ {name}")
