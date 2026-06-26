"""AI Arena - 导航调试v2"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    errors = []
    logs = []
    page.on("console", lambda msg: (errors if msg.type == "error" else logs).append(f"[{msg.type}] {msg.text}"))
    
    page.goto("http://127.0.0.1:8077/")
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    
    # Check App object
    print("=== App Check ===")
    app_exists = page.evaluate('typeof App !== "undefined"')
    print(f"  App exists: {app_exists}")
    current = page.evaluate("App.currentPage")
    print(f"  currentPage: {current}")
    
    # Direct navigateTo call
    print("\n=== Direct navigateTo('scenarios') ===")
    page.evaluate("App.navigateTo('scenarios')")
    time.sleep(0.5)
    current = page.evaluate("App.currentPage")
    print(f"  currentPage: {current}")
    active = page.evaluate("Array.from(document.querySelectorAll('.page')).map(function(p) { return p.id + ':' + p.classList.contains('active') + ':' + getComputedStyle(p).display; })")
    for a in active:
        print(f"  {a}")
    
    # Direct navigateTo settings
    print("\n=== Direct navigateTo('settings') ===")
    page.evaluate("App.navigateTo('settings')")
    time.sleep(0.5)
    current = page.evaluate("App.currentPage")
    print(f"  currentPage: {current}")
    active = page.evaluate("Array.from(document.querySelectorAll('.page')).map(function(p) { return p.id + ':' + p.classList.contains('active') + ':' + getComputedStyle(p).display; })")
    for a in active:
        print(f"  {a}")
    
    # Try clicking
    print("\n=== Click scenarios button ===")
    page.evaluate("App.navigateTo('config')")
    time.sleep(0.3)
    page.click('[data-page="scenarios"]', timeout=5000)
    time.sleep(0.5)
    current = page.evaluate("App.currentPage")
    print(f"  currentPage: {current}")
    
    # Console errors
    print("\n=== Errors ===")
    for e in errors:
        print(f"  {e}")
    
    browser.close()
