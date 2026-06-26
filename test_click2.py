"""Check click handler"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    logs = []
    page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
    page.goto("http://127.0.0.1:8077/")
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    
    print("=== Before click ===")
    print("currentPage:", page.evaluate("App.currentPage"))
    navigating = page.evaluate("App._navigating")
    print("_navigating:", navigating, type(navigating))
    
    # Use page.click with proper selector
    btn = page.query_selector('[data-page="scenarios"]')
    if btn:
        btn.click()
        time.sleep(1)
    
    print("=== After click ===")
    print("currentPage:", page.evaluate("App.currentPage"))
    for l in logs:
        print(l)
    
    browser.close()
