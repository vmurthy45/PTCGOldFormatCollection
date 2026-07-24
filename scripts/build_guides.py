"""Convert every markdown piloting guide into data/guides.json, keyed by the
same slug the site's JS uses to match a guide to a deck (see slug() in index.html):

    deck.toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'')

A guide file's own title doesn't always match the deck name used in the card
data (e.g. the file titled "Perfection (Mewtwo & Mew-GX) (2019)" belongs to
the deck named "Perfection Mewtwo (2019)" in the collection spreadsheet).
MANUAL_SLUG_OVERRIDES maps those specific files to the correct deck slug.
"""
import json
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
GUIDES_DIR = ROOT / "piloting_guides_collection"
CARDS_JSON = ROOT / "data" / "cards.json"
OUT = ROOT / "data" / "guides.json"

MANUAL_SLUG_OVERRIDES = {
    "2019/Perfection_Mewtwo_2019.md": "perfection_mewtwo_2019",
}


def slug(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def title_to_slug(h1: str) -> str:
    h1 = re.sub(r"^How to Pilot\s*[—-]\s*", "", h1).strip()
    return slug(h1)


def main():
    deck_names = {c["deck"] for c in json.loads(CARDS_JSON.read_text(encoding="utf-8"))}
    deck_slugs = {slug(d) for d in deck_names}

    guides = {}
    files = sorted(GUIDES_DIR.glob("*/*.md"))
    for path in files:
        rel = str(path.relative_to(GUIDES_DIR))
        text = path.read_text(encoding="utf-8")
        h1_match = re.search(r"^#\s+(.+)$", text, re.M)
        if not h1_match:
            raise SystemExit(f"No H1 title found in {rel}")

        key = MANUAL_SLUG_OVERRIDES.get(rel) or title_to_slug(h1_match.group(1))
        if key not in deck_slugs:
            raise SystemExit(f"{rel}: computed slug '{key}' doesn't match any deck in cards.json")

        guides[key] = markdown.markdown(text, extensions=["extra"])

    missing = deck_slugs - guides.keys()
    OUT.write_text(json.dumps(guides, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(guides)} guides to {OUT}")
    if missing:
        print(f"Decks with no guide yet ({len(missing)}): {sorted(missing)}")


if __name__ == "__main__":
    main()
