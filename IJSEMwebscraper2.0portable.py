# -*- coding: utf-8 -*-
"""IJSEMwebscraper1.8portable.py

Standard python implementation of IJSEMwebscraper1.7_debug.ipynb Jupyter
notebook implementation but with added spacy AI detection for strains, basionyms, organism names and accession
numbers. Two step search for accession numbers NER and Regex plus filtering to remove non-INSDC accessions.
This .py version is a streamlined version of the script that others
can execute.


Run:
    python IJSEMwebscraper1.8.py <BASE_FILENAME>

Environment (optional):
    DEBUG_NER=1
    DEBUG_URL_LIMIT=3
"""
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import glob
from pathlib import Path
# Resolve Chrome/ChromeDriver paths in a user-portable way (uses Selenium cache when available)
def _pick_newest(paths):
    paths = [p for p in paths if p and Path(p).exists()]
    if not paths:
        return None
    return str(max(paths, key=lambda p: Path(p).stat().st_mtime))

def resolve_cached_chrome():
    home = str(Path.home())
    candidates = glob.glob(f"{home}/.cache/selenium/chrome/**/chrome", recursive=True)
    return _pick_newest(candidates)

def resolve_cached_chromedriver():
    home = str(Path.home())
    candidates = glob.glob(f"{home}/.cache/selenium/chromedriver/**/chromedriver", recursive=True)
    return _pick_newest(candidates)

chrome_path = resolve_cached_chrome()
chromedriver_path = resolve_cached_chromedriver()

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd
import re
import os
import glob
from pathlib import Path
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
input_file = base_filename + ".htm"
alldescriptions = base_filename + ".txt"
output = base_filename + ".xlsx"


# --- Baseline 1.6 changes: load trained NER model once + organism NER + debug helpers ---
# Trained entity labels: "strain", "accession", "organism", "basionym"

nlp_strain = spacy.load(r"./output/model-best")  # trained model (shared)

ALLOWED_STRAIN_LABELS = {"strain"}
ALLOWED_ORGANISM_LABELS = {"organism"}
ALLOWED_BASIONYM_LABELS = {"basionym"}
ALLOWED_ACCESSION_LABELS = {"accession"}

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


def find_basionyms(description):
    """
    Find basionym entities using the trained spaCy NER model.
    Returns only entities labeled 'basionym' (de-duplicated).
    """
    if not description:
        return []

    results = []
    doc2 = nlp_strain(description)
    for ent in doc2.ents:
        if ent.label_ in ALLOWED_BASIONYM_LABELS:
            val = ent.text.strip()
            val = val.encode("ascii", "ignore").decode("utf-8", errors="ignore").strip()
            if val and val not in results:
                results.append(val)
    return results


# Debug controls
DEBUG_NER = False
DEBUG_URL_LIMIT = 200  # only debug first N URLs encountered
DEBUG_DESC_PER_URL = 200  # debug only first N descriptions per URL

_debug_seen_urls = set()
_debug_desc_count = {}

# Prefixes we explicitly do NOT want to report (not INSDC sequence accessions)
_NON_INSDC_PREFIXES = (
    "GCA_", "GCF_",  # GenColl/Assembly accessions
    "PRJNA", "PRJEB", "PRJDB",  # BioProject
    "SAMN", "SAME", "SAMD",  # BioSample
)

# INSDC-like accession patterns (sequence records)
_INSDC_REGEXES = [
    re.compile(r"^[A-Z]{1,2}\d{5,8}$", re.I),
    re.compile(r"^[A-Z]{4}\d{8}$", re.I),
    re.compile(r"^[A-Z]{6}\d{9}$", re.I),
    re.compile(r"^[A-Z]{2}_[A-Z]{2}\d{6,}$", re.I),
    re.compile(r"^[A-Z]{2}_[A-Z]{4}\d{8}$", re.I),
]


def find_accessions(description: str):
    """Return only 'accession' entities from the trained model (no gating)."""
    if not description:
        return []
    results = []
    doc2 = nlp_strain(description)
    for ent in doc2.ents:
        if ent.label_ in ALLOWED_ACCESSION_LABELS:
            val = _clean_ascii(ent.text.strip())
            if val and val not in results:
                results.append(val)
    return results


def filter_insdc_accessions(values):
    """Filter accession strings to INSDC-like sequence accessions only.

    Removes BioProject/BioSample/Assembly/GenColl-style IDs and other non-INSDC identifiers.
    Strips version suffixes like '.1'.
    """
    if not values:
        return []
    out = []
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if not s or s.lower() == "nan":
            continue
        s = s.rstrip(".,);")
        s = re.sub(r"\.[0-9]+$", "", s)

        if s.upper().startswith(_NON_INSDC_PREFIXES):
            continue

        if any(rx.match(s) for rx in _INSDC_REGEXES):
            if s not in out:
                out.append(s)
    return out


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

def remove_non_ascii(text):
    """Remove non-ASCII characters"""
    return ''.join(char for char in text if ord(char) < 128)


# alternative Beautifiul soup with autodetect encoding
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

# (Moved strain/organism NER functions above for clarity; this cell is now unused in the debug notebook.)

from selenium.webdriver.common.by import By
import tempfile

pub_df = pd.DataFrame(
    columns=['PublishedName', 'Accessions', 'Strains', 'Basionym', 'Authority', 'DOI', 'filtered_url'])
pd.set_option('display.max_columns', None)
combined_description = []

for filtered_url in filtered_urls:
    temp_profile = tempfile.mkdtemp()

    options = Options()
    # Only set binary_location if we actually found a Chrome binary for this user
    if chrome_path and os.path.exists(chrome_path):
        options.binary_location = chrome_path
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Use cached chromedriver when available; otherwise let Selenium decide
    if chromedriver_path and os.path.exists(chromedriver_path):
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(180)
    driver.set_script_timeout(180)

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
    basionym = []

    # Navigate to the webpage
    driver.get(filtered_url)
    try:
        WebDriverWait(driver, 120).until(lambda d: d.execute_script("return document.readyState") in ("interactive","complete"))
        WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except TimeoutException:
        pass

    # Allow time for dynamic content to load (you may need to use WebDriverWait for more robust waiting)
    time.sleep(3)

    # Robust page_source retrieval (avoid renderer timeouts on slow pages)
    try:
        html = driver.page_source
    except TimeoutException:
        # Fallback: grab outer HTML via JS (often succeeds even when page_source times out)
        html = driver.execute_script('return document.documentElement.outerHTML;')

    for element in driver.find_elements(By.CLASS_NAME, "item-meta-data__item-title"):
        # print(element.text)
        title = element.text
        # print(title)

    for element in driver.find_elements(By.PARTIAL_LINK_TEXT, "doi.org"):
        doi = element.text
        # print(doi)

    # find publication year
    for element in driver.find_elements(By.XPATH,
                                        "//*[@id='bellowheadercontainer']/main/div[2]/div/ul/li[3]/span/span[2]"):
        date = element.text
        year = date[-4:]
        # print(year)

    # find authors
    for element in driver.find_elements(By.XPATH, "//*[@id='bellowheadercontainer']/main/div[2]/div/ul/li[1]/span"):
        author_raw = element.text
        # print(author_raw)
        author = re.sub(r"[\d+]+", '', author_raw)
        author = re.sub(r"†", '', author)
        author = re.sub(r" and ", ',', author)
        author = re.sub(r",,", ',', author)
        author = author.split(',')
        author[:] = [item for item in author if item != '']
        # print(author)
        author_count = len(author)
        # print(author_count)
        if author_count == 1:
            name1 = (str(author[0]))
            name1 = HumanName(name1)
            authority = name1.last + ' ' + str(year)
            # print(authority)
        elif author_count == 2:
            name1 = (str(author[0]))
            name1 = HumanName(name1)
            name2 = (str(author[1]))
            name2 = HumanName(name2)
            authority = name1.last + ' and ' + name2.last + ' ' + str(year)
            # print(authority)
        else:
            name1 = (str(author[0]))
            name1 = HumanName(name1)
            authority = name1.last + ' et al. ' + str(year)
            # print(authority)

    # extract data from each species description
    for element in driver.find_elements(By.CSS_SELECTOR, "div.tl-main-part.title"):  # finds section headers
        # print(element.text)
        counter += 1
        description = element.text
        # print(description)
        if "Description of" in description:
            strains = []
            # print('found', description)
            # snumber = 's' + str(counter - 4) + '/p[3]'
            snumber = 's' + str(counter - 4)
            # print('snumber is', snumber)
            for element in driver.find_elements(By.ID, snumber):
                description = element.text
                cleaned_text = remove_non_ascii(description)
                combined_description.append(cleaned_text)
                debug_ner(cleaned_text, url=filtered_url, header='Description block (debug)')
                # print(cleaned_text)
                # print(description)

                # find the organism names (NER - label 'organism')
                orgname = find_organisms(cleaned_text)

                # find accessions via NER (then post-process to INSDC only)
                accessions = filter_insdc_accessions(find_accessions(cleaned_text))

                # Fallback: regex extraction if NER misses (still filtered to INSDC)
                if not accessions and description is not None:
                    pattern = [r'[A-Z]{2}\d{6}', r'[A-Z]{4}\d{8}', r'([A-Z]+)(_[A-Z]+)\d{6}', r'[A-Z]{6}\d{9}']
                    regex = re.compile(r'\b(' + '|'.join(pattern) + r')\b')
                    accessions = filter_insdc_accessions([m.group() for m in regex.finditer(description)])
                    # print('accessions', accessions)

                # find the strains
                if description is not None:
                    strains = find_strains(cleaned_text)
                    # print('strain names', strains)

                # find the basionyms
                basionym = find_basionyms(cleaned_text) if description is not None else []

                # load data into pandas dataframe
                row_data = [orgname, accessions, strains, basionym, authority, doi, filtered_url]
                length = len(pub_df)
                pub_df.loc[length] = row_data
            # print('BREAK1')

    for element in driver.find_elements(By.CLASS_NAME, "tl-lowest-section"):  # finds section headers
        description1 = element.text
        outer_html = element.get_attribute("outerHTML")
        if "Description of" in description1:
            # print(outer_html)
            spans = soup.find_all('span', attrs={'class': 'tl-lowest-section'})
            for span in spans:
                if "Description of" in span.text:
                    # print (span.text)
                    outer_div_id = span.find_parent('div').get('id')
                    # print(f"Outer div ID: {outer_div_id}, Text: {span.text}")
                    for element in driver.find_elements(By.ID, outer_div_id):
                        description = element.text
                        cleaned_text = remove_non_ascii(description)
                        combined_description.append(cleaned_text)
                    debug_ner(cleaned_text, url=filtered_url, header='Description block (debug)')
                    # print(cleaned_text)
                    # print(description)

                    # find the organism names (NER - label 'organism')
                    orgname = find_organisms(cleaned_text)

                    # find accessions via NER (then post-process to INSDC only)
                    accessions = filter_insdc_accessions(find_accessions(cleaned_text))

                    # Fallback: regex extraction if NER misses (still filtered to INSDC)
                    if not accessions and description is not None:
                        pattern = [r'[A-Z]{2}\d{6}', r'[A-Z]{4}\d{8}', r'([A-Z]+)(_[A-Z]+)\d{6}', r'[A-Z]{6}\d{9}']
                        regex = re.compile(r'\b(' + '|'.join(pattern) + r')\b')
                        accessions = filter_insdc_accessions([m.group() for m in regex.finditer(description)])
                        # print('accessions', accessions)

                    # find the strains
                    strains = []
                    if description is not None:
                        strains = find_strains(cleaned_text)
                        # print('strain names', strains)

                    # find the basionyms
                    basionym = find_basionyms(cleaned_text) if description is not None else ""

                    basionym_list = find_basionyms(cleaned_text)
                    basionym_for_row = ", ".join(basionym_list) if basionym_list else ""

                    # load data into pandas dataframe
                    row_data = [orgname, accessions, strains, basionym, authority, doi, filtered_url]
                    length = len(pub_df)
                    pub_df.loc[length] = row_data
                    # print('BREAK2')

    # Close the browser window
    driver.quit()

# optional write description to a file
# print(combined_description)
file = open(alldescriptions, "w")
file.writelines(combined_description)
file.close()


def non_empty_list(x):
    return isinstance(x, list) and len(x) > 0


pub_df = pub_df[
    pub_df["PublishedName"].apply(non_empty_list) &
    pub_df["Accessions"].apply(non_empty_list)
    ]

print("Rows after organism + accession filter:", pub_df.shape)

pub_df

pd.set_option('max_colwidth', None)
# pub_df['Strains'] = [', '.join(map(str, l)) for l in pub_df['Strains']]
# pub_df['Strains'] = pub_df['Strains'].astype(pd.StringDtype())
# pub_df['Strains'] = pub_df['Strains'].str.replace(',', ', ')

pub_df = pub_df.copy()

pub_df.loc[:, 'Strains'] = pub_df['Strains'].apply(
    lambda l: ", ".join(map(str, l)) if isinstance(l, list) else ""
)

pub_df.loc[:, 'Strains'] = pub_df['Strains'].astype(pd.StringDtype())
pub_df.loc[:, 'Strains'] = pub_df['Strains'].str.replace(',', ', ')

pub_df["Basionym"] = pub_df["Basionym"].apply(lambda x: ", ".join(x) if isinstance(x, list) and len(x) > 0 else "")
pub_df.explode(['PublishedName']).reset_index(drop=True)
pub2_df = pub_df.explode(['Accessions']).reset_index(drop=True)
pub4_df = pub2_df.explode(['PublishedName']).reset_index(drop=True)
pub4_df.rename(columns={'Accessions': 'accession'}, inplace=True)
pub4_df = pub4_df[
    pub4_df['accession'].isnull() | ~pub4_df[pub4_df['accession'].notnull()].duplicated(subset='accession', keep='first')]


df_unique = pub4_df.drop_duplicates(["accession"], keep="first")
# df_unique = df_unique.dropna()
df_unique


# df_unique['accession'] = df_unique['accession'].astype('str')
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
srcchk_df

combine_df = pd.merge(left=pub4_df, right=srcchk_df, left_on='accession', right_on='accession', how='outer')
combine_df = combine_df[
    ['PublishedName', 'NCBIname', 'Strains', 'accession', 'strain', 'Basionym', 'Authority', 'taxid', 'DOI',
     'filtered_url']]

# Ensure PublishedName is string for sorting
combine_df['PublishedName'] = combine_df['PublishedName'].astype(str)

# Sort alphabetically (case-insensitive)
combine_df = combine_df.sort_values(
    by='PublishedName',
    key=lambda col: col.str.lower(),
    na_position='last'
).reset_index(drop=True)

combine_df


def highlight_rows(row):
    ijsemvalue = row.loc['PublishedName']
    ncbivalue = row.loc['NCBIname']
    if ijsemvalue != ncbivalue:
        color = '#FFB3BA'  # Red
    elif ijsemvalue == ncbivalue:
        color = '#BAFFC9'  # Green
    return ['background-color: {}'.format(color) for r in row]


new_df = combine_df.style.apply(highlight_rows, axis=1, subset=['PublishedName', 'NCBIname'])

new_df.to_excel(output, engine='xlsxwriter', index=False, na_rep='')

print("\n")
print("Script complete output saved as", output)


