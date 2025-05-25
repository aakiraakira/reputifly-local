#!/usr/bin/env python3
"""
map_scrape.py

Usage:
  python map_scrape.py "YOUR QUERY HERE"
  python map_scrape.py "maid agency singapore" --headless

This script:
 1. Opens Google Maps for your query
 2. Disables images & sets a large viewport for faster loads
 3. Locates the left-hand results pane via multiple fallbacks
 4. Scrolls the pane until Google signals end-of-list or no more new items
 5. Extracts the full pane.text dump
 6. Saves to: <sanitized_query>_dump.txt
 7. Prints the filename for your front end to pick up
"""

import time
import argparse
import urllib.parse
import os

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def sanitize_filename(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.strip().lower())


def init_driver(headless: bool):
    opts = uc.ChromeOptions()
    if headless:
        opts.headless = True
    # speed & stealth flags
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--blink-settings=imagesEnabled=false")  # disable images
    opts.add_argument("--window-size=1920,1080")               # large viewport
    opts.add_argument("--disable-dev-shm-usage")               # stability
    return uc.Chrome(options=opts)


def find_results_pane(driver, timeout=20):
    selectors = [
        (By.CSS_SELECTOR, "div.widget-pane-content.scrollable-y"),
        (By.CSS_SELECTOR, "div.section-layout.section-scrollbox.scrollable-y"),
        (By.XPATH, "//div[@role='feed']"),
        (By.XPATH, "//div[@role='region']"),
    ]
    for by, sel in selectors:
        try:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, sel))
            )
        except TimeoutException:
            continue
    raise RuntimeError("Could not locate the Maps results pane; selectors may need updating.")


def scroll_until_end(driver, pane, timeout=90, pause=1.0):
    last_h = driver.execute_script("return arguments[0].scrollHeight", pane)
    start = time.time()
    while True:
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", pane)
        time.sleep(pause)
        new_h = driver.execute_script("return arguments[0].scrollHeight", pane)
        text = pane.text
        # detect Google end-of-list message
        if "reached the end of the list" in text.lower():
            break
        # if no height change and timed out
        if new_h == last_h and time.time() - start > timeout:
            break
        last_h = new_h


def main():
    parser = argparse.ArgumentParser(description="Headless Google Maps scraper for SG queries")
    parser.add_argument("query", help="Search term (e.g. 'cleaning services singapore') — include 'singapore'")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    args = parser.parse_args()

    driver = init_driver(headless=args.headless)
    base_url = "https://www.google.com/maps/search/"
    try:
        url = base_url + urllib.parse.quote_plus(args.query) + "/"
        driver.get(url)

        pane = find_results_pane(driver, timeout=30)
        scroll_until_end(driver, pane, timeout=90, pause=1.0)

        # raw dump
        raw = pane.text
        fname = sanitize_filename(args.query) + "_dump.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(raw)

        print(fname)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
