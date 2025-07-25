# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 13:49:04 2025

@author: mcveigh
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

service = Service("/net/snowman/vol/export2/mcveigh.cache/selenium/chromedriver")

# Print the path to the driver
print(f"Using ChromeDriver from: {service}")

driver = webdriver.Chrome(service=service)
driver.get("https://www.google.com")
print(driver.title)
driver.quit()