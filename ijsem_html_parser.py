#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IJSEM directory parser with original row-building flow preserved.

Only the input source changed:
- instead of Selenium page_source, it reads saved HTML files from INPUT_HTML_DIR.
- Change required due to modified security settings IJSEM put in place to block
  programmatic access of the full text of their publications

Key behavior:
- Organism/accession extraction is done ONLY inside matched "Description of" blocks.
- Each matched block starts with fresh local variables.
- The main path is div.tl-main-part.title.
- tl-lowest-section is only a fallback when the main path finds no Description of block.
- The rest of the pipeline stays close to IJSEMwebscraper2.0.py:
  pub_df -> acclist -> srcchk -> combine_df -> highlight_rows -> Excel
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from charset_normalizer import from_path
from nameparser import HumanName
import spacy
from spacy.matcher import PhraseMatcher

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
INPUT_HTML_DIR = Path("/net/snowman/vol/export2/mcveigh/notebook/ijsem-clean/input")
OUTPUT_DIR = Path("/net/snowman/vol/export2/mcveigh/notebook/ijsem-clean/output-ijsem")
OUTPUT_XLSX = OUTPUT_DIR / "ijsem_html_dir_output.xlsx"
COMBINED_DESCRIPTION_TXT = OUTPUT_DIR / "ijsem_combined_descriptions.txt"

SPACY_BASE_MODEL = "en_core_web_md"
SPACY_TRAINED_MODEL = "./output/model-best"

DEBUG_NER = False
DEBUG_URL_LIMIT = 200
DEBUG_DESC_PER_URL = 200

# -------------------------------------------------------------------
# Model loading
# -------------------------------------------------------------------
nlp = spacy.load(SPACY_BASE_MODEL)
nlp_strain = spacy.load(SPACY_TRAINED_MODEL)

ALLOWED_STRAIN_LABELS = {"strain"}
ALLOWED_ORGANISM_LABELS = {"organism"}
ALLOWED_BASIONYM_LABELS = {"basionym"}
ALLOWED_ACCESSION_LABELS = {"accession"}

phrase_matcher = PhraseMatcher(nlp.vocab)
strain_keywords = ["strain", "Strain", "strains", "Strains"]
patterns = [nlp.make_doc(p) for p in strain_keywords]
phrase_matcher.add("STRAIN_CTX", patterns)

_debug_seen_urls = set()
_debug_desc_count = {}

_NON_INSDC_PREFIXES = ("GCA_", "GCF_", "PRJNA", "PRJEB", "PRJDB", "SAMN", "SAME", "SAMD")
_INSDC_REGEXES = [
    re.compile(r"^[A-Z]{1,2}\d{5,8}$", re.I),
    re.compile(r"^[A-Z]{4}\d{8}$", re.I),
    re.compile(r"^[A-Z]{6}\d{9}$", re.I),
    re.compile(r"^[A-Z]{2}_[A-Z]{2}\d{6,}$", re.I),
    re.compile(r"^[A-Z]{2}_[A-Z]{4}\d{8}$", re.I),
]


def _clean_ascii(s: str) -> str:
    return s.encode("ascii", "ignore").decode("utf-8", errors="ignore").strip()


def remove_non_ascii(text):
    return "".join(char for char in text if ord(char) < 128)


def find_strains(description: str):
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


def find_accessions(description: str):
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
    basionyms = find_basionyms(description)
    accessions = filter_insdc_accessions(find_accessions(description))

    print(f"\n=== {header or 'debug'} ===")
    print("TEXT:", description[:1200])
    print("ORG:", orgs)
    print("STRAIN:", strains)
    print("BASIONYM:", basionyms)
    print("ACCESSIONS:", accessions)


def read_html_file(path: Path):
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        best = from_path(str(path)).best()
        text = str(best) if best is not None else raw.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(text, "html.parser")
    return text, soup


def extract_meta(soup: BeautifulSoup, source_path: Path):
    published_name = ""
    doi = ""
    year = ""
    authority = ""

    title_meta = soup.find("meta", attrs={"name": "citation_title"}) or soup.find("meta", attrs={"property": "og:title"})
    if title_meta and title_meta.get("content"):
        published_name = title_meta.get("content").strip()
    else:
        title_el = soup.select_one(".item-meta-data__item-title")
        if title_el:
            published_name = title_el.get_text(" ", strip=True)

    doi_meta = soup.find("meta", attrs={"name": "citation_doi"})
    if doi_meta and doi_meta.get("content"):
        doi = doi_meta.get("content").replace("doi:", "").strip()
    else:
        doi_link = soup.select_one('a[href*="doi.org"]')
        if doi_link:
            doi = doi_link.get_text(" ", strip=True) or doi_link.get("href", "").strip()

    year_meta = soup.find("meta", attrs={"name": "citation_year"}) or soup.find("meta", attrs={"name": "citation_date"})
    if year_meta and year_meta.get("content"):
        y = year_meta.get("content").strip()
        year = y[-4:] if len(y) >= 4 else y

    authors = [m.get("content", "").strip() for m in soup.find_all("meta", attrs={"name": "citation_author"}) if m.get("content")]
    if authors and year:
        if len(authors) == 1:
            name1 = HumanName(authors[0])
            authority = f"{name1.last} {year}"
        elif len(authors) == 2:
            name1 = HumanName(authors[0])
            name2 = HumanName(authors[1])
            authority = f"{name1.last} and {name2.last} {year}"
        else:
            name1 = HumanName(authors[0])
            authority = f"{name1.last} et al. {year}"

    url_meta = soup.find("meta", attrs={"property": "og:url"})
    filtered_url = url_meta.get("content").strip() if url_meta and url_meta.get("content") else str(source_path)

    return published_name, doi, authority, filtered_url


def add_description_row(cleaned_text: str, filtered_url: str, authority: str, doi: str, pub_df: pd.DataFrame, combined_description: list[str]):
    """Extract only from a matched 'Description of' block and append one row."""
    combined_description.append(cleaned_text)
    debug_ner(cleaned_text, url=filtered_url, header="Description block (debug)")

    # IMPORTANT: reset per block so there is no carry-over between descriptions.
    orgname = []
    accessions = []
    strains = []
    basionym = []

    orgname = find_organisms(cleaned_text)
    accessions = filter_insdc_accessions(find_accessions(cleaned_text))

    if not accessions:
        pattern = [r"[A-Z]{2}\d{6}", r"[A-Z]{4}\d{8}", r"([A-Z]+)(_[A-Z]+)\d{6}", r"[A-Z]{6}\d{9}"]
        regex = re.compile(r"\b(" + "|".join(pattern) + r")\b")
        accessions = filter_insdc_accessions([m.group() for m in regex.finditer(cleaned_text)])

    strains = find_strains(cleaned_text)
    basionym = find_basionyms(cleaned_text)

    row_data = [orgname, accessions, strains, basionym, authority, doi, filtered_url]
    pub_df.loc[len(pub_df)] = row_data


def main() -> int:
    INPUT_HTML_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    html_files = sorted(list(INPUT_HTML_DIR.glob("*.html")) + list(INPUT_HTML_DIR.glob("*.mhtml")))
    if not html_files:
        print(f"No .html/.htm files found in {INPUT_HTML_DIR}")
        return 1

    print(f"Found {len(html_files)} HTML files in {INPUT_HTML_DIR}")

    pub_df = pd.DataFrame(
        columns=["PublishedName", "Accessions", "Strains", "Basionym", "Authority", "DOI", "filtered_url"]
    )
    combined_description = []

    for source_path in html_files:
        html, soup = read_html_file(source_path)
        published_name, doi, authority, filtered_url = extract_meta(soup, source_path)

        print(f"\nProcessing: {source_path.name}")

        # Scope to the article body when available so page chrome / related content
        # do not shift the title-to-section mapping.
        article_root = soup.select_one("#html_fulltext") or soup.select_one("#itemFullTextId") or soup

        seen_section_ids = set()
        found_main_description = False

        # Primary path: div.tl-main-part.title
        counter = 1
        for element in article_root.select("div.tl-main-part.title"):
            counter += 1
            description = element.get_text(" ", strip=True)
            if "Description of" not in description:
                continue

            found_main_description = True
            snumber = "s" + str(counter - 3)
            if snumber in seen_section_ids:
                continue

            target = article_root.find(id=snumber)
            if target is None:
                continue

            seen_section_ids.add(snumber)
            cleaned_text = remove_non_ascii(target.get_text(" ", strip=True))
            add_description_row(cleaned_text, filtered_url, authority, doi, pub_df, combined_description)

        # Fallback: only if the primary path found no Description of section.
        if not found_main_description:
            for element in article_root.select("span.tl-lowest-section"):
                description1 = element.get_text(" ", strip=True)
                if "Description of" not in description1:
                    continue

                parent_div = element.find_parent("div")
                if parent_div is None or not parent_div.get("id"):
                    continue

                outer_div_id = parent_div.get("id")
                if outer_div_id in seen_section_ids:
                    continue

                target = article_root.find(id=outer_div_id)
                if target is None:
                    continue

                seen_section_ids.add(outer_div_id)
                cleaned_text = remove_non_ascii(target.get_text(" ", strip=True))
                add_description_row(cleaned_text, filtered_url, authority, doi, pub_df, combined_description)

    if combined_description:
        COMBINED_DESCRIPTION_TXT.write_text("\n\n".join(combined_description), encoding="utf-8")

    def non_empty_list(x):
        return isinstance(x, list) and len(x) > 0

    pub_df = pub_df[
        pub_df["PublishedName"].apply(non_empty_list) &
        pub_df["Accessions"].apply(non_empty_list)
    ].copy()

    print("Rows after organism + accession filter:", pub_df.shape)

    if pub_df.empty:
        combine_df = pd.DataFrame(columns=["PublishedName", "NCBIname", "Strains", "accession", "strain", "Basionym", "Authority", "taxid", "DOI", "filtered_url"])
        with pd.ExcelWriter(OUTPUT_XLSX, engine="xlsxwriter") as writer:
            combine_df.to_excel(writer, index=False, sheet_name="results")
        print("\n")
        print("Script complete output saved as", OUTPUT_XLSX)
        return 0

    pub_df = pub_df.copy()
    pub_df.loc[:, "Strains"] = pub_df["Strains"].apply(lambda l: ", ".join(map(str, l)) if isinstance(l, list) else "")
    pub_df.loc[:, "Strains"] = pub_df["Strains"].astype(pd.StringDtype())
    pub_df.loc[:, "Strains"] = pub_df["Strains"].str.replace(",", ", ")
    pub_df["Basionym"] = pub_df["Basionym"].apply(lambda x: ", ".join(x) if isinstance(x, list) and len(x) > 0 else "")

    pub_df = pub_df.explode(["PublishedName"]).reset_index(drop=True)
    pub2_df = pub_df.explode(["Accessions"]).reset_index(drop=True)
    pub4_df = pub2_df.explode(["PublishedName"]).reset_index(drop=True)
    pub4_df.rename(columns={"Accessions": "accession"}, inplace=True)
    pub4_df = pub4_df[
        pub4_df["accession"].isnull() | ~pub4_df[pub4_df["accession"].notnull()].duplicated(subset="accession", keep="first")
    ]

    df_unique = pub4_df.drop_duplicates(["accession"], keep="first")
    df_unique.loc[:, "accession"] = df_unique["accession"].astype("str")

    with open("acclist", "w", encoding="utf-8") as f:
        for text in df_unique["accession"].tolist():
            f.write(text + "\n")

    os.system("/netopt/ncbi_tools64/bin/srcchk -i acclist -f taxname,taxid,strain -o acclist.taxdata")

    taxdata_file_name = "acclist.taxdata"
    if not os.path.exists(taxdata_file_name) or os.path.getsize(taxdata_file_name) == 0:
        print("acclist.taxdata is empty; skipping srcchk merge.")
        srcchk_df = pd.DataFrame(columns=["accession", "NCBIname", "taxid", "strain"])
    else:
        srcchk_df = pd.read_csv(taxdata_file_name, sep="\t", index_col=None, low_memory=False)
        if "Unnamed: 4" in srcchk_df.columns:
            srcchk_df.drop(columns=["Unnamed: 4"], inplace=True)
        if "organism" in srcchk_df.columns:
            srcchk_df.rename(columns={"organism": "NCBIname"}, inplace=True)
        srcchk_df["accession"] = srcchk_df["accession"].astype(str).replace(r"\.\d+", "", regex=True).astype(str)
        if "NCBIname" in srcchk_df.columns:
            srcchk_df = srcchk_df.dropna(subset=["NCBIname"])

    combine_df = pd.merge(left=pub4_df, right=srcchk_df, left_on="accession", right_on="accession", how="outer")
    combine_df = combine_df[
        ["PublishedName", "NCBIname", "Strains", "accession", "strain", "Basionym", "Authority", "taxid", "DOI", "filtered_url"]
    ]

    combine_df["PublishedName"] = combine_df["PublishedName"].astype(str)
    combine_df = combine_df.sort_values(
        by="PublishedName",
        key=lambda col: col.str.lower(),
        na_position="last"
    ).reset_index(drop=True)

    def highlight_rows(row):
        ijsemvalue = row.loc["PublishedName"]
        ncbivalue = row.loc["NCBIname"]
        if ijsemvalue != ncbivalue:
            color = "#FFB3BA"
        else:
            color = "#BAFFC9"
        return [f"background-color: {color}" for _ in row]

    new_df = combine_df.style.apply(highlight_rows, axis=1, subset=["PublishedName", "NCBIname"])
    new_df.to_excel(OUTPUT_XLSX, engine="xlsxwriter", index=False, na_rep="")

    print("\n")
    print("Script complete output saved as", OUTPUT_XLSX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
