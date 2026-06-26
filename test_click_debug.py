"""Check what element is at the button position"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://127.0.0.1:8077/")
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    
    # Get button position
    pos = page.evaluate('document.querySelector("[data-page=scenarios]").getBoundingClientRect()')
    print(f"Button pos: x={pos['x']}, y={pos['y']}, w={pos['width']}, h={pos['height']}")
    
    x = pos['x'] + pos['width'] / 2
    y = pos['y'] + pos['height'] / 2
    print(f"Click at ({x}, {y})")
    
    # Check what element is at that position
    el_info = page.evaluate(f'document.elementFromPoint({x}, {y}).tagName + " | " + document.elementFromPoint({x}, {y}).className + " | " + document.elementFromPoint({x}, {y}).id')
    print(f"Element at click point: {el_info}")
    
    # Check parent elements
    result = page.evaluate(f"""
        (function() {{
            var el = document.elementFromPoint({x}, {y});
            var chain = [];
            while (el && chain.length < 8) {{
                chain.push(el.tagName + '.' + el.className.toString().substring(0,30));
                el = el.parentElement;
            }}
            return chain.join(' -> ');
        }})()
    """)
    print(f"Element chain: {result}")
    
    browser.close()
