#!/usr/bin/env python3
"""Simulate GitHub Pages project-site subpath serving and verify the app renders."""
import sys
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8899/intenda/"
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1200)
    root_children = page.evaluate("document.getElementById('root').childElementCount")
    body_text = page.evaluate("document.body.innerText.length")
    theme = page.evaluate("document.documentElement.dataset.theme")
    print("root_children:", root_children)
    print("body_text_len:", body_text)
    print("theme:", theme)
    page.screenshot(path="/home/hatch/workspace/.pages-sim/night.png")
    # toggle to day mode
    page.locator("button", has_text="日间").first.click()
    page.wait_for_timeout(600)
    theme2 = page.evaluate("document.documentElement.dataset.theme")
    print("theme_after_toggle:", theme2)
    page.screenshot(path="/home/hatch/workspace/.pages-sim/day.png")
    print("page_errors:", errors)
    browser.close()

ok = root_children > 0 and body_text > 200 and not errors
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
