"""AI Arena - 导航调试"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}"))
    
    page.goto("http://127.0.0.1:8077/")
    page.wait_for_load_state("networkidle")
    
    # 打印初始状态
    print("=== 初始状态 ===")
    active = page.evaluate("""
        Array.from(document.querySelectorAll('.page')).map(p => ({
            id: p.id,
            active: p.classList.contains('active'),
            display: getComputedStyle(p).display
        }))
    """)
    for p in active:
        print(f"  {p['id']}: active={p['active']}, display={p['display']}")
    
    # 检查导航按钮
    print("\n=== 导航按钮 ===")
    buttons = page.evaluate("""
        Array.from(document.querySelectorAll('.nav-btn')).map(b => ({
            text: b.textContent.trim(),
            page: b.dataset.page,
            visible: b.offsetParent !== null,
            rect: b.getBoundingClientRect()
        }))
    """)
    for b in buttons:
        print(f"  {b['page']}: text='{b['text']}', visible={b['visible']}, rect={b['rect']}")
    
    # 尝试直接用 JS 调用 navigateTo
    print("\n=== 直接调用 navigateTo('scenarios') ===")
    result = page.evaluate("App.navigateTo('scenarios'); return App.currentPage")
    print(f"  currentPage after: {result}")
    
    active = page.evaluate("""
        Array.from(document.querySelectorAll('.page')).map(p => ({
            id: p.id,
            active: p.classList.contains('active'),
            display: getComputedStyle(p).display
        }))
    """)
    for p in active:
        print(f"  {p['id']}: active={p['active']}, display={p['display']}")
    
    # 再试一个
    print("\n=== 直接调用 navigateTo('arena') ===")
    result = page.evaluate("App.navigateTo('arena'); return App.currentPage")
    print(f"  currentPage after: {result}")
    
    active = page.evaluate("""
        Array.from(document.querySelectorAll('.page')).map(p => ({
            id: p.id,
            active: p.classList.contains('active'),
            display: getComputedStyle(p).display
        }))
    """)
    for p in active:
        print(f"  {p['id']}: active={p['active']}, display={p['display']}")
    
    # 检查 console 输出
    print("\n=== 控制台输出 ===")
    for e in errors:
        print(f"  {e}")
    
    browser.close()
