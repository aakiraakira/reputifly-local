#!/usr/bin/env python3
"""
map_scrape.py

Usage:
  python map_scrape.py "YOUR QUERY HERE"
  python map_scrape.py "maid agency singapore" --headless

This script:
  1. Opens Google Maps for your query
  2. Locates the left-hand results pane (via multiple fallbacks)
  3. JS-scrolls it until “You’ve reached the end of the list” (or no more new items)
  4. Extracts pane.text (all visible listings)
  5. Saves to: <sanitized_query>_dump.txt
"""

import time
import argparse
import urllib.parse
import os

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def sanitize_filename(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.strip().lower())

def init_driver(headless: bool):
    opts = uc.ChromeOptions()
    if headless:
        opts.headless = True

    # ─────── BLOCK IMAGES ───────
    # (prevents Chrome from downloading any images on the page)
    prefs = {"profile.managed_default_content_settings.images": 2}
    opts.add_experimental_option("prefs", prefs)

    # stealth flags
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    return uc.Chrome(options=opts)

def find_results_pane(driver, timeout=20):
    candidates = [
        (By.CSS_SELECTOR, "div.widget-pane-content.scrollable-y"),      # older Maps
        (By.CSS_SELECTOR, "div.section-layout.section-scrollbox.scrollable-y"),  # newer Maps
        (By.CSS_SELECTOR, "div.section-scrollbox"),                      # fallback
        (By.XPATH, "//div[@role='feed']"),                              # feed role
        (By.XPATH, "//div[@role='region']")                             # region role
    ]
    for by, sel in candidates:
        try:
            pane = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, sel))
            )
            return pane
        except Exception:
            pass
    raise RuntimeError("❌ Could not locate the Maps results pane; selectors may need updating.")

def scroll_until_end(driver, pane, timeout=60, pause=0.1):
    """
    JS-scroll the pane until:
      • pane.text contains “You’ve reached the end of the list”
      • OR scrollHeight stops increasing
      • OR timeout
    Uses a very short pause between scrolls for speed.
    """
    last_h = driver.execute_script("return arguments[0].scrollHeight", pane)
    start  = time.time()

    while True:
        # scroll to bottom
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", pane)
        time.sleep(pause)

        new_h = driver.execute_script("return arguments[0].scrollHeight", pane)
        txt   = pane.text

        if "You've reached the end of the list" in txt:
            break
        if new_h == last_h:
            break
        if time.time() - start > timeout:
            break

        last_h = new_h

def main():
    parser = argparse.ArgumentParser(description="Headless Google Maps scraper")
    parser.add_argument("query", help="Search term (e.g. 'cleaning services')")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    args = parser.parse_args()

    driver = init_driver(headless=args.headless)

    url = "https://www.google.com/maps/search/" + urllib.parse.quote_plus(args.query) + "/"
    driver.get(url)

    pane = find_results_pane(driver, timeout=30)
    # pause reduced from 1.0 → 0.1 to speed up scrolling
    scroll_until_end(driver, pane, timeout=75, pause=0.1)

    text = pane.text
    fname = sanitize_filename(args.query) + "_dump.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(text)

    driver.quit()
    # print the filename so your server.py can pick it up
    print(fname)

if __name__ == "__main__":
    main()
