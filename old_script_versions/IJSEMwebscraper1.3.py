
# -*- coding: utf-8 -*-
"""
Created on Mon Aug  4 10:30:36 2025

Refactored selenium scraper for IJSEM articles.
Uses temporary Chrome profiles to avoid session conflicts.
Includes strain extraction with spaCy and NCBI taxonomy checks.

@author: mcveigh
"""

import os
import sys
import time
import re
import spacy
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from urllib.parse import urljoin
from openpyxl import Workbook

# --- Setup ---

# Custom spaCy model (adjust path if needed)
print("Loading spaCy models...")
nlp = spacy.load("strain-ner-model-best")

# Chrome binary location (verified)
CHROME_BINARY = "/home/mcveigh/.cache/selenium/chrome/linux64/138.0.7204.183/chrome"

# --- Functions ---

def get_webdriver():
    options = Options()
    options.binary_location = CHROME_BINARY
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except WebDriverException as e:
        print("❌ WebDriver initialization failed.")
        print(f"Error: {e}")
        return None

def extract_urls_from_html(filename):
    with open(filename, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    return list({link.get("href") for link in soup.find_all("a", href=True) if "10.1099/ijsem" in link.get("href")})

def extract_text_from_url(url, driver):
    try:
        driver.get(url)
        time.sleep(3)  # Adjust as needed based on page load time
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        article_body = soup.find("div", class_="article__body")
        return article_body.get_text(separator=" ") if article_body else ""
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return ""

def find_strains(text):
    doc = nlp(text)
    return sorted(set(ent.text for ent in doc.ents if ent.label_ == "STRAIN"))

def get_tax_ids(strains):
    tax_ids = {}
    for strain in strains:
        url = f"https://api.ncbi.nlm.nih.gov/taxonomy/v0/taxonomy/{strain}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data and "taxonomy" in data and data["taxonomy"]:
                    tax_ids[strain] = data["taxonomy"][0].get("tax_id", "")
        except Exception:
            pass
    return tax_ids

def write_results_to_excel(results, output_file):
    wb = Workbook()
    ws = wb.active
    ws.append(["URL", "Strain Name", "NCBI TaxID"])

    for url, strain_data in results.items():
        for strain, taxid in strain_data.items():
            ws.append([url, strain, taxid or "Not Found"])

    wb.save(output_file)

# --- Main Execution ---

if len(sys.argv) != 2:
    print("Usage: python IJSEMwebscraper1.3.py <html_input_file>")
    sys.exit(1)

input_file = sys.argv[1]
print(f"Reading input file {input_file} and extracting URLs...")
urls = extract_urls_from_html(input_file)
print(f"Found {len(urls)} URLs:\n" + "\n".join(urls))

all_results = {}

for i, url in enumerate(urls, 1):
    print(f"\n[{i}/{len(urls)}] Processing URL: {url}")
    driver = get_webdriver()
    if driver is None:
        print(f"Skipping URL due to WebDriver error: {url}")
        continue

    text = extract_text_from_url(url, driver)
    driver.quit()

    if not text:
        print(f"No text extracted from {url}")
        continue

    strains = find_strains(text)
    tax_ids = get_tax_ids(strains)
    all_results[url] = tax_ids

# Output Excel file
output_excel = input_file + "_strain_report.xlsx"
write_results_to_excel(all_results, output_excel)
print(f"\n✅ Results written to {output_excel}")
