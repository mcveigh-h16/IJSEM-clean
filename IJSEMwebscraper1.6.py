# -*- coding: utf-8 -*-
"""
Created on Tues Feb 24 14:26:06 2026

Standard python implementation of IJSEMwebscraper1.6_debug.ipynb Jupyter
notebook implementation includes spacy AI detection for strains and organism names.
This .py version is a streamlined version of the script that others
can execute.

Selenium .cache files are quite large and need to be cleaned up periodically.

@author: mcveigh
"""
import sys

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
chrome_path = "/home/mcveigh/.cache/selenium/chrome/linux64/138.0.7204.183/chrome"

from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import re
import os
import sys
import bs4
from bs4 import BeautifulSoup
import numpy as np
from nameparser import HumanName
import spacy

# Base model used for sentence segmentation / general parsing
# nlp = spacy.load("en_core_web_sm")
nlp = spacy.load("en_core_web_md")

# Load your trained NER model ONCE (new training set has multiple entity types)
nlp_strain = spacy.load(r"./output/model-best")  # load once, not inside function


from spacy.matcher import PhraseMatcher
from spacy import displacy  # kept, but not required for extraction

base_filename = sys.argv[1]
input = base_filename + ".htm"
alldescriptions = base_filename + ".txt"
output = base_filename + ".xlsx"

# Debug controls
DEBUG_NER = False
DEBUG_URL_LIMIT = 200          # only debug first N URLs encountered
DEBUG_DESC_PER_URL = 200       # debug only first N descriptions per URL

_debug_seen_urls = set()
_debug_desc_count = {}

# alternative BeautifulSoup with autodetect encoding
from charset_normalizer import from_path

# Auto-detect file encoding
result = from_path(input).best()
# NOTE: keeping your original behavior unchanged.
html = str(result)

# --- Parse with BeautifulSoup ---
soup = BeautifulSoup(html, "html.parser")
text = soup.get_text()

# Extract all http/https links
urls = re.findall(r"https?://\S+", text)
urls = [url.rstrip('.,);') for url in urls]

# Filter links as needed
filtered_urls = [
    url for url in urls
    if all(exclude not in url for exclude in ["TandC", "myaccount", "join-the-society"])
]

if not filtered_urls:
    raise ValueError("No usable URLs found!")

print(f"Found {len(filtered_urls)} URLs:")
print("\n".join(filtered_urls))


# --- Baseline 1.6 changes: load trained NER model once + organism NER + debug helpers ---
# Trained entity labels: "strain", "accession", "organism", "basionym"

nlp_strain = spacy.load(r"./output/model-best")  # trained model (shared)

ALLOWED_STRAIN_LABELS = {"strain"}
ALLOWED_ORGANISM_LABELS = {"organism"}

# PhraseMatcher used to gate strain extraction to sentences mentioning strain keywords
phrase_matcher = PhraseMatcher(nlp.vocab)
strain_keywords = ["strain", "Strain", "strains", "Strains"]
patterns = [nlp.make_doc(p) for p in strain_keywords]
phrase_matcher.add("STRAIN_CTX", patterns)

def _clean_ascii(s: str) -> str:
    return s.encode("ascii", "ignore").decode("utf-8", errors="ignore").strip()

def find_strains(description: str):
    """Return only 'strain' entities from the trained model (sentence-gated)."""
    if not description:
        return []
    results = []
    doc = nlp(description)
    for sent in doc.sents:
        if not phrase_matcher(nlp(sent.text)):
            continue
        doc2 = nlp_strain(sent.text)
        for ent in doc2.ents:
            if ent.label_ in ALLOWED_STRAIN_LABELS:
                val = _clean_ascii(ent.text.strip())
                if val and val not in results:
                    results.append(val)
    return results

def find_organisms(description: str):
    """Return only 'organism' entities from the trained model (no gating)."""
    if not description:
        return []
    results = []
    doc2 = nlp_strain(description)
    for ent in doc2.ents:
        if ent.label_ in ALLOWED_ORGANISM_LABELS:
            val = _clean_ascii(ent.text.strip())
            if val and val not in results:
                results.append(val)
    return results

from IPython.display import display, HTML

def debug_ner(description: str, *, url: str = "", header: str = ""):
    """Visualize entities from the trained model and show extracted lists."""
    if not DEBUG_NER:
        return
    if url and url not in _debug_seen_urls and len(_debug_seen_urls) >= DEBUG_URL_LIMIT:
        return

    if url:
        _debug_desc_count.setdefault(url, 0)
        if _debug_desc_count[url] >= DEBUG_DESC_PER_URL:
            return
        _debug_desc_count[url] += 1
        _debug_seen_urls.add(url)

    orgs = find_organisms(description)
    strains = find_strains(description)

    # Show a short snippet of the description to orient debugging
    snippet = (description[:1500] + "…") if len(description) > 1500 else description
    snippet_html = f"<details><summary><b>Description text (click to expand)</b></summary><pre>{snippet}</pre></details>"

    display(HTML(title_html + url_html + lists_html + snippet_html))
    # Render entities inline
    display(HTML(displacy.render(doc2, style="ent")))

def remove_non_ascii(text):
    """Remove non-ASCII characters"""
    return ''.join(char for char in text if ord(char) < 128)

"""
Main body - Selenium to extract data from html
"""
from selenium.webdriver.common.by import By
import tempfile
pub_df = pd.DataFrame(columns=['PublishedName', 'Accessions', 'Strains', 'Authority', 'DOI', 'filtered_url'])
pd.set_option('display.max_columns', None)
combined_description = []

for filtered_url in filtered_urls:
    temp_profile = tempfile.mkdtemp()

    options = Options()
    options.binary_location = chrome_path
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    counter = 1
    strains = []
    accessions = []
    orgname = []
    doi = []
    author = []
    date = []
    year = []
    author_raw = []
    author = []
    name1 = []
    name2 = []
    author_count = []
    authority = []
    description = None
    description1 = []
    description2 = []
    snumber = []

    # Navigate to the webpage
    driver.get(filtered_url)

    # Allow time for dynamic content to load
    time.sleep(3)

    html = driver.page_source

    for element in driver.find_elements(By.CLASS_NAME, "item-meta-data__item-title"):
        title = element.text

    for element in driver.find_elements(By.PARTIAL_LINK_TEXT, "doi.org"):
        doi = element.text

    # find publication year
    for element in driver.find_elements(By.XPATH, "//*[@id='bellowheadercontainer']/main/div[2]/div/ul/li[3]/span/span[2]"):
        date = element.text
        year = date[-4:]

    # find authors
    for element in driver.find_elements(By.XPATH, "//*[@id='bellowheadercontainer']/main/div[2]/div/ul/li[1]/span"):
        author_raw = element.text
        author = re.sub(r"[\d+]+", '', author_raw)
        author = re.sub(r"†", '', author)
        author = re.sub(r" and ", ',', author)
        author = re.sub(r",,", ',', author)
        author = author.split(',')
        author[:] = [item for item in author if item != '']
        author_count = len(author)

        if author_count == 1:
            name1 = (str(author[0]))
            name1 = HumanName(name1)
            authority = name1.last + ' ' + str(year)
        elif author_count == 2:
            name1 = (str(author[0]))
            name1 = HumanName(name1)
            name2 = (str(author[1]))
            name2 = HumanName(name2)
            authority = name1.last + ' and ' + name2.last + ' ' + str(year)
        else:
            name1 = (str(author[0]))
            name1 = HumanName(name1)
            authority = name1.last + ' et al. ' + str(year)

    # extract data from each species description
    for element in driver.find_elements(By.CSS_SELECTOR, "div.tl-main-part.title"):  # finds section headers
        counter += 1
        description = element.text
        if "Description of" in description:
            strains = []  # reset per description section
            snumber = 's' + str(counter - 4)
            for element in driver.find_elements(By.ID, snumber):
                description = element.text
                cleaned_text = remove_non_ascii(description)
                combined_description.append(cleaned_text)

                # NEW: organism name via NER (replaces regex)
                orgname = find_organisms(cleaned_text)

                # find the accessions (keep regex for baseline stability)
                pattern = [r'[A-Z]{2}\d{6}', r'[A-Z]{4}\d{8}', r'([A-Z]+)(_[A-Z]+)\d{6}', r'[A-Z]{6}\d{9}']
                regex = re.compile(r'\b(' + '|'.join(pattern) + r')\b')
                if description is not None:
                    accessions = [m.group() for m in regex.finditer(description)]

                # strain via NER (baseline behavior)
                if description is not None:
                    strains = find_strains(cleaned_text)

                # load data into pandas dataframe
                row_data = [orgname, accessions, strains, authority, doi, filtered_url]
                length = len(pub_df)
                pub_df.loc[length] = row_data

    for element in driver.find_elements(By.CLASS_NAME, "tl-lowest-section"):  # finds section headers
        description1 = element.text
        outer_html = element.get_attribute("outerHTML")
        if "Description of" in description1:
            spans = soup.find_all('span', attrs={'class': 'tl-lowest-section'})
            for span in spans:
                if "Description of" in span.text:
                    outer_div_id = span.find_parent('div').get('id')
                    for element in driver.find_elements(By.ID, outer_div_id):
                        description = element.text
                        cleaned_text = remove_non_ascii(description)
                        combined_description.append(cleaned_text)

                    # NEW: organism name via NER (replaces regex)
                    orgname = find_organisms(cleaned_text)

                    # find the accessions (keep regex)
                    pattern = [r'[A-Z]{2}\d{6}', r'[A-Z]{4}\d{8}', r'([A-Z]+)(_[A-Z]+)\d{6}', r'[A-Z]{6}\d{9}']
                    regex = re.compile(r'\b(' + '|'.join(pattern) + r')\b')
                    if description is not None:
                        accessions = [m.group() for m in regex.finditer(description)]

                    # strain via NER
                    strains = []
                    if description is not None:
                        strains = find_strains(cleaned_text)

                    # load data into pandas dataframe
                    row_data = [orgname, accessions, strains, authority, doi, filtered_url]
                    length = len(pub_df)
                    pub_df.loc[length] = row_data

    # Close the browser window
    driver.quit()

"""
optional write description to a file
"""
file = open(alldescriptions, "w")
file.writelines(combined_description)
file.close()

"""
Pandas to analyze extracted data
"""
def non_empty_list(x):
    return isinstance(x, list) and len(x) > 0

pub_df = pub_df[
    pub_df["PublishedName"].apply(non_empty_list) &
    pub_df["Accessions"].apply(non_empty_list)
]

print("Rows after organism + accession filter:", pub_df.shape)

pd.set_option('max_colwidth', None)
pub_df['Strains'] = [', '.join(map(str, l)) for l in pub_df['Strains']]
pub_df['Strains'] = pub_df['Strains'].astype(pd.StringDtype())
pub_df['Strains'] = pub_df['Strains'].str.replace(',', ', ')
pub_df.explode(['PublishedName']).reset_index(drop=True)
pub2_df = pub_df.explode(['Accessions']).reset_index(drop=True)
pub4_df = pub2_df.explode(['PublishedName']).reset_index(drop=True)
pub4_df.rename(columns={'Accessions': 'accession'}, inplace=True)
pub4_df = pub4_df[pub4_df['accession'].isnull() | ~pub4_df[pub4_df['accession'].notnull()].duplicated(subset='accession', keep='first')]

df_unique = pub4_df.drop_duplicates(["accession"], keep="first")
df_unique.loc[:, 'accession'] = df_unique['accession'].astype('str')

with open('acclist', 'w') as f:
    for text in df_unique['accession'].tolist():
        f.write(text + '\n')

os.system("/netopt/ncbi_tools64/bin/srcchk -i acclist -f taxname,taxid,strain -o acclist.taxdata")

taxdata_file_name = (r'acclist.taxdata')
srcchk_df = pd.read_csv(taxdata_file_name, sep='\t', index_col=None, low_memory=False)
srcchk_df.drop(columns=['Unnamed: 4'], inplace=True)
srcchk_df.rename(columns={'organism': 'NCBIname'}, inplace=True)
srcchk_df['accession'] = srcchk_df['accession'].astype(str).replace('\.\d+', '', regex=True).astype(str)
srcchk_df = srcchk_df.dropna(subset=['NCBIname'])

combine_df = pd.merge(left=pub4_df, right=srcchk_df, left_on='accession', right_on='accession', how='outer')
combine_df = combine_df[['PublishedName', 'NCBIname', 'Strains', 'accession', 'strain', 'Authority', 'taxid', 'DOI', 'filtered_url']]
# Ensure PublishedName is string for sorting
combine_df['PublishedName'] = combine_df['PublishedName'].astype(str)

# Sort alphabetically (case-insensitive)
combine_df = combine_df.sort_values(
    by='PublishedName',
    key=lambda col: col.str.lower(),
    na_position='last'
).reset_index(drop=True)


def highlight_rows(row):
    ijsemvalue = row.loc['PublishedName']
    ncbivalue = row.loc['NCBIname']
    if ijsemvalue != ncbivalue:
        color = '#FFB3BA'  # Red
    elif ijsemvalue == ncbivalue:
        color = '#BAFFC9'  # Green
    return ['background-color: {}'.format(color) for r in row]

new_df = combine_df.style.apply(highlight_rows, axis=1, subset=['PublishedName', 'NCBIname'])
new_df

new_df.to_excel(output, engine='xlsxwriter', index=False, na_rep='')

print("\n")
print("Script complete output saved as", output)