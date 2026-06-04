#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bulk URL extractor. Use Beautiful Soup to extract URLs from a single HTML file saved from IJSEM weekly publication.
usage:
    python bulk_url_extractor.py <base_filename>
    Outputs a text file <base_filename>.txt with one URL per line. This can be used with BULK URL Opener extension in Chrome.
"""
import os
import sys
import re
import bs4
from bs4 import BeautifulSoup

base_filename = sys.argv[1]
input_file = base_filename + ".htm"
output = base_filename + ".txt"

#alternative Beautifiul soup with autodetect encoding
from charset_normalizer import from_path

# Auto-detect file encoding
result = from_path(input_file).best()
html = str(result)

# Parse with BeautifulSoup
soup = BeautifulSoup(html, "html.parser")
text = soup.get_text()

# Extract all http/https links
urls = re.findall(r"https?://\S+", text)
urls = [url.rstrip('.,);') for url in urls]

# Filter links as needed
filtered_urls = [
    url for url in urls
    if all(exclude not in url for exclude in ["TandC", "myaccount", "join-the-society"])
    # Remove "doi.org" from filter if you want article links
]

if not filtered_urls:
    raise ValueError("No usable URLs found!")

print(f"Found {len(filtered_urls)} URLs:")
print("\n".join(filtered_urls))

with open(output, "w") as f:
    f.write("\n".join(filtered_urls))
f.close()