"""Test event delegation"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    logs = []
    page.on("console", lambda msg: logs.append(msg.text))
    page.goto("http://127.0.0.1:8077/")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    
    # Check if event delegation works
    page.evaluate('console.log("--- Testing event delegation ---")')
    page.evaluate('var menu = document.querySelector(".navbar-menu"); console.log("menu:", menu ? "found" : "not found")')
    page.evaluate('var btn = document.querySelector("[data-page=scenarios]"); console.log("btn:", btn ? btn.outerHTML.substring(0,80) : "not found")')
    page.evaluate('console.log("closest:", document.querySelector("[data-page=scenarios]").closest(".nav-btn") ? "yes" : "no")')
    page.evaluate('document.querySelector("[data-page=scenarios]").dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}))')
    time.sleep(1)
    
    print("currentPage:", page.evaluate("App.currentPage"))
    for l in logs:
        print(l)
    
    browser.close()
