# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 14:30:05 2025

@author: mcveigh
"""

from selenium.webdriver.chrome.options import Options

options = Options()
print("Chrome binary (before setting):", options.binary_location)

# explicitly set Linux Chrome path
options.binary_location = "/usr/bin/google-chrome"
print("Chrome binary (after setting):", options.binary_location)
