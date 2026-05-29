# -*- coding: utf-8 -*-
"""
Created on February 10, 2026

@author: mcveigh
"""

# -*- coding: utf-8 -*-
"""
Created on February 10, 2026

Converts .json annotations from label-studio to spacy annotations. 
This version strips flanking spaces from annotations and also resolves overlapping
annotations defaulting to the longest. Effective for cleaning the json file prior to the
conversion to spacy. 

Also converts all labels to lower case for better training. 

@author: mcveigh
"""

import json
import spacy
from spacy.tokens import DocBin

INPUT_FILE = "training_annotations.json"      # your Label Studio export
OUTPUT_FILE = "training_annotations.spacy"    # output file
LANG = "en"

nlp = spacy.blank(LANG)
doc_bin = DocBin(store_user_data=True)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

def extract_entities(item):
    """
    Extract (start, end, label) from Label Studio format
    """
    entities = []
    for ann in item.get("annotations", []):
        if ann.get("was_cancelled"):
            continue

        for res in ann.get("result", []):
            if res.get("type") != "labels":
                continue

            val = res.get("value", {})
            start = val.get("start")
            end = val.get("end")
            labels = val.get("labels", [])

            if start is None or end is None or not labels:
                continue

            label = labels[0]  # usually single label
            label = label.lower()
            entities.append((start, end, label))

    return entities

def trim_span_offsets(text: str, start: int, end: int):
    """
    Trim leading/trailing whitespace inside [start, end) by adjusting offsets.
    Returns (new_start, new_end) or (None, None) if the span becomes empty/invalid.
    """
    if start is None or end is None:
        return None, None
    if start < 0 or end > len(text) or start >= end:
        return None, None

    # Trim leading whitespace
    while start < end and text[start].isspace():
        start += 1
    # Trim trailing whitespace (end is exclusive)
    while end > start and text[end - 1].isspace():
        end -= 1

    if start >= end:
        return None, None
    return start, end

def keep_longest_non_overlapping(entities):
    """
    Given a list of (start, end, label) char spans, remove overlaps keeping the longest.
    Greedy strategy: sort by length desc, then earlier start, then earlier end.
    Keep a span if it doesn't overlap any already kept span.
    """
    # Sort: longest first
    ents_sorted = sorted(
        entities,
        key=lambda x: (-(x[1] - x[0]), x[0], x[1], x[2])
    )

    kept = []
    for s, e, label in ents_sorted:
        overlaps = False
        for ks, ke, _ in kept:
            # overlap if ranges intersect: [s,e) and [ks,ke)
            if s < ke and ks < e:
                overlaps = True
                break
        if not overlaps:
            kept.append((s, e, label))

    # Optional: return in reading order
    kept.sort(key=lambda x: (x[0], x[1]))
    return kept

skipped = 0
processed = 0

for item in data:
    text = item.get("data", {}).get("text", "")
    if not text.strip():
        continue

    raw_entities = extract_entities(item)

    # 1) Trim whitespace around entity spans
    trimmed_entities = []
    for start, end, label in raw_entities:
        ts, te = trim_span_offsets(text, start, end)
        if ts is None:
            skipped += 1
            continue
        trimmed_entities.append((ts, te, label))

    # 2) Remove overlaps, keeping the longest span
    trimmed_entities = keep_longest_non_overlapping(trimmed_entities)

    doc = nlp.make_doc(text)

    spans = []
    for start, end, label in trimmed_entities:
        span = doc.char_span(
            start,
            end,
            label=label,
            alignment_mode="contract"
        )
        if span is None:
            skipped += 1
            continue
        spans.append(span)

    # 3) Extra safety: spaCy-level overlap filtering based on tokenization
    #    (char-level spans can become token-overlapping after "contract")
    spans = sorted(spans, key=lambda s: (-(s.end - s.start), s.start, s.end, s.label_))
    filtered = []
    for sp in spans:
        if any(sp.start < f.end and f.start < sp.end for f in filtered):
            continue
        filtered.append(sp)
    filtered.sort(key=lambda s: (s.start, s.end))

    doc.ents = filtered
    doc_bin.add(doc)
    processed += 1

doc_bin.to_disk(OUTPUT_FILE)

print(f"Processed docs: {processed}")
print(f"Skipped entities: {skipped}")
print(f"Saved to: {OUTPUT_FILE}")
