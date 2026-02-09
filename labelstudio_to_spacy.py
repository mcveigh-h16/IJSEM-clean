import json
import spacy
from spacy.tokens import DocBin


INPUT_FILE = "data.json"      # your Label Studio export
OUTPUT_FILE = "train.spacy"  # output file
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

        # Skip cancelled or empty annotations
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

            label = labels[0]   # usually single label

            entities.append((start, end, label))

    return entities


skipped = 0
processed = 0


for item in data:

    text = item.get("data", {}).get("text", "")

    if not text.strip():
        continue

    entities = extract_entities(item)

    doc = nlp.make_doc(text)

    spans = []

    for start, end, label in entities:

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

    doc.ents = spans
    doc_bin.add(doc)

    processed += 1


doc_bin.to_disk(OUTPUT_FILE)

print(f"Processed docs: {processed}")
print(f"Skipped entities: {skipped}")
print(f"Saved to: {OUTPUT_FILE}")
