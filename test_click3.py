"""Test click via JS"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    logs = []
    page.on("console", lambda msg: logs.append(msg.text))
    page.goto("http://127.0.0.1:8077/")
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    
    # Check button has event listener by dispatching click
    page.evaluate('console.log("TEST: before dispatch")')
    page.evaluate('document.querySelector("[data-page=scenarios]").dispatchEvent(new Event("click", {bubbles: true}))')
    time.sleep(1)
    
    print("currentPage:", page.evaluate("App.currentPage"))
    for l in logs:
        print(l)
    
    browser.close()
