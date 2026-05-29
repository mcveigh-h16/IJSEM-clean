#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Single-URL Chrome smoke test for IJSEM.

What this checks:
- Chrome starts successfully
- the article page loads
- a normal cookie banner can be clicked automatically
- a Cloudflare challenge is detected and pauses for manual completion
- after the pause, the script re-reads the DOM and prints key markers

Usage:
    python ijsem_chrome_smoke_test.py
"""

from __future__ import annotations

import time
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

URL = "https://www.microbiologyresearch.org/content/journal/ijsem/10.1099/ijsem.0.007124"
OUT_HTML = Path("ijsem_chrome_smoke_test.html")
OUT_TEXT = Path("ijsem_chrome_smoke_test.txt")

CLOUDFLARE_MARKERS = [
    "Just a moment...",
    "Performing security verification",
    "Verify you are human",
    "Enable JavaScript and cookies to continue",
    "Ray ID:",
    "Cloudflare",
]

COOKIE_LABELS = [
    "accept",
    "accept all",
    "i agree",
    "agree",
    "allow all cookies",
    "ok",
]


def cloudflare_present(html: str) -> bool:
    low = (html or "").lower()
    return any(marker.lower() in low for marker in CLOUDFLARE_MARKERS)


def accept_cookie_banner(driver, timeout=8):
    """Best-effort click on common cookie consent buttons."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            candidates = driver.find_elements(By.TAG_NAME, "button") + driver.find_elements(By.TAG_NAME, "a")
            for el in candidates:
                try:
                    txt = (el.text or "").strip().lower()
                except Exception:
                    continue
                if txt and any(lbl in txt for lbl in COOKIE_LABELS):
                    try:
                        el.click()
                        print("Accepted cookie banner via:", txt)
                        return True
                    except Exception:
                        pass
        except Exception:
            pass
        time.sleep(0.5)
    return False


def build_driver() -> webdriver.Chrome:
    options = Options()
    # Keep the browser visible so you can manually clear Cloudflare if needed.
    # Uncomment the next line only if you explicitly want headless mode.
    # options.add_argument("--headless")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Let Selenium Manager pick the matching Chrome/driver already working in your environment.
    driver = webdriver.Chrome(options=options)
    return driver


def main() -> int:
    driver = build_driver()
    try:
        print("Chrome browser version:", driver.capabilities.get("browserVersion"))
        print("Chrome driver info:", driver.capabilities.get("chrome", {}))

        print("\nLoading URL:", URL)
        driver.get(URL)
        time.sleep(4)

        # Try cookie banner first.
        accept_cookie_banner(driver, timeout=8)
        time.sleep(2)

        html = driver.execute_script("return document.documentElement.outerHTML")
        print("Initial current_url:", driver.current_url)
        print("Initial title:", driver.title)
        print("Cloudflare present initially:", cloudflare_present(html))

        if cloudflare_present(html):
            print("\nCloudflare challenge detected.")
            print("Solve the challenge in the browser window, then press Enter here.")
            input()
            time.sleep(2)
            html = driver.execute_script("return document.documentElement.outerHTML")
            print("After manual step current_url:", driver.current_url)
            print("After manual step title:", driver.title)
            print("Cloudflare present after manual step:", cloudflare_present(html))

        # Save the final page state
        OUT_HTML.write_text(html, encoding="utf-8")
        text = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
        OUT_TEXT.write_text(text, encoding="utf-8")

        print("\nSaved:", OUT_HTML)
        print("Saved:", OUT_TEXT)
        print("Final html length:", len(html))
        print("Final text length:", len(text))

        # Print the key article markers
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1.item-meta-data__item-title")
        abstract = soup.select_one("#abstract_content")
        fulltext = soup.select_one("#itemFullTextId")
        html_fulltext = soup.select_one("#html_fulltext")

        print("\n--- Checks ---")
        print("article title present:", bool(title))
        print("abstract present:", bool(abstract))
        print("itemFullTextId present:", bool(fulltext))
        print("html_fulltext present:", bool(html_fulltext))

        if title:
            print("title text:", title.get_text(" ", strip=True))
        if abstract:
            print("abstract text preview:", abstract.get_text(" ", strip=True)[:600])
        if fulltext:
            print("itemFullTextId data-fullTexturl:", fulltext.get("data-fullTexturl") or fulltext.get("data-fulltexturl"))

        # A small line-by-line preview for visual confirmation.
        print("\n--- HTML preview ---")
        for i, line in enumerate(html.splitlines()[:120], 1):
            print(f"{i:05d}: {line}")

        return 0

    except WebDriverException as exc:
        print("WebDriverException:", exc)
        return 1
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
