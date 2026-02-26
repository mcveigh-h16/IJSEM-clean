# -*- coding: utf-8 -*-
"""
Created on Mon Aug  4 11:35:32 2025

@author: mcveigh
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

chrome_path = "/home/mcveigh/.cache/selenium/chrome/linux64/138.0.7204.183/chrome"

options = Options()
options.binary_location = chrome_path
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

print("Launching Chrome WebDriver...")

try:
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.google.com")
    print("✅ WebDriver test passed.")
    print("Page title is:", driver.title)
    driver.quit()
except WebDriverException as e:
    print("❌ WebDriver test failed.")
    print("Message:", e)
