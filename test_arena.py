"""Debug Arena loading"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    errors = []
    page.on("console", lambda msg: errors.append(msg.text))
    page.goto("http://127.0.0.1:8077/")
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    
    print("Arena type:", page.evaluate("typeof Arena"))
    print("Arena defined?", page.evaluate("typeof Arena !== 'undefined'"))
    
    # Check what globals exist
    result = page.evaluate("Object.keys(window).filter(k => k[0] === k[0].toUpperCase() && typeof window[k] === 'object').sort()")
    print("Global objects:", result[:20])
    
    # Check if there's a parsing error by evaluating the file content
    result = page.evaluate("""
        fetch('/static/js/components/arena.js')
            .then(r => r.text())
            .then(code => {
                try {
                    new Function(code);
                    return 'OK - no syntax error';
                } catch(e) {
                    return 'SYNTAX ERROR: ' + e.message;
                }
            })
    """)
    print("arena.js parse:", result)
    
    # Check console output
    page.evaluate("console.log('=== All console output ===')")
    for e in errors:
        print("  ", e)
    
    browser.close()
