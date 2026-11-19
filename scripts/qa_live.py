#!/usr/bin/env python3
"""Live check of the deployed Intenda site: renders, theme toggles, screenshots."""
import sys
from playwright.sync_api import sync_playwright

URL = "https://toniadreal.github.io/intenda/"
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3500)
    root_children = page.evaluate("document.getElementById('root').childElementCount")
    body_text = page.evaluate("document.body.innerText.length")
    theme = page.evaluate("document.documentElement.dataset.theme")
    print("root_children:", root_children)
    print("body_text_len:", body_text)
    print("theme:", theme)
    page.screenshot(path="/home/hatch/workspace/.pages-sim/live_night.png")
    page.locator("button", has_text="夜间").first.click()
    page.wait_for_timeout(800)
    theme2 = page.evaluate("document.documentElement.dataset.theme")
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    print("theme_after_toggle:", theme2)
    print("body_bg_day:", bg)
    page.screenshot(path="/home/hatch/workspace/.pages-sim/live_day.png")
    print("page_errors:", errors)
    browser.close()

ok = root_children > 0 and body_text > 200 and theme2 == "day"
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
