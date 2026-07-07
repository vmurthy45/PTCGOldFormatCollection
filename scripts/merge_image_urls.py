"""Merge card_collection_with_urls.csv (Name, Set, Set Code, Image URL) into
data/cards.json by (name, set), adding an "image" field to each row.

The CSV has 692 unique (name, set) pairs covering all but 10 of the 701 pairs
in cards.json. The 10 gaps are all basic Energy rows recorded with no set
number (e.g. plain "Water Energy") plus one row with a mojibake name
("Pok√©mon Catcher" — a UTF-8/Latin-1 mangling of "Pokémon Catcher" that
crept into the original spreadsheet); those rows simply get no image.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS_JSON = ROOT / "data" / "cards.json"
CSV_PATH = ROOT / "card_collection_with_urls.csv"

# Fix the mojibake name so it lines up with the CSV's clean spelling.
NAME_FIXES = {
    "Pok√©mon Catcher": "Pokémon Catcher",
}


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    url_by_key = {}
    for r in rows:
        url_by_key[(r["Name"], r["Set"])] = r["Image URL"]

    cards = json.loads(CARDS_JSON.read_text(encoding="utf-8"))

    matched = 0
    for c in cards:
        name = NAME_FIXES.get(c["name"], c["name"])
        c["name"] = name
        url = url_by_key.get((name, c["set"]))
        if url:
            c["image"] = url
            matched += 1

    CARDS_JSON.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Matched images for {matched}/{len(cards)} rows ({len(cards) - matched} without an image, mostly basic Energy with no set number)")


if __name__ == "__main__":
    main()
