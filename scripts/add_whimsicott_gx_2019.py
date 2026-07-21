"""One-off: add the Whimsicott GX (2019) decklist to data/cards.json.

Set numbers are the printings legal in Standard 2019 (SUM-on through
Unified Minds) and were HTTP-verified against pokemontcg.io before adding
(see scripts/merge_image_urls.py URL_OVERRIDES for the image mapping).
Shared cards (Mew, Rare Candy, etc.) reuse the exact (name, set) pairs
already present in the collection so they pick up existing images; the
one exception is Rainbow Energy, whose only in-collection prints are
XY-era (not 2019-legal), so it uses the Celestial Storm 151/168 print.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS_JSON = ROOT / "data" / "cards.json"
YEAR = "2019"
DECK = "Whimsicott GX (2019)"

NEW_ROWS = [
    # Pokémon (19)
    (4, "Cottonee", "139/214"),
    (3, "Whimsicott GX", "140/214"),
    (1, "Blitzle", "81/214"),
    (1, "Zebstrika", "82/214"),
    (3, "Porygon", "155/214"),
    (4, "Porygon-Z", "157/214"),
    (1, "Mew", "76/214"),
    (1, "Whimsicott", "144/236"),
    (1, "Ditto Prism Star", "154/214"),
    # Trainers (27)
    (4, "Rare Candy", "129/149"),
    (4, "Counter Catcher", "91/111"),
    (4, "Pokémon Communication", "152/181"),
    (1, "Fairy Charm L", "172/214"),
    (1, "Wondrous Labyrinth", "158/181"),
    (1, "Reset Stamp", "206/236"),
    (2, "Cherish Ball", "191/236"),
    (4, "Professor Elm's Lecture", "188/214"),
    (4, "Cynthia", "119/156"),
    (2, "Tate & Liza", "148/168"),
    # Energy (14)
    (1, "Rainbow Energy", "151/168"),
    (1, "Fairy Energy", ""),
    (4, "Unit Energy FDF", "118/131"),
    (4, "Recycle Energy", "212/236"),
    (4, "Triple Acceleration Energy", "190/214"),
]


def main():
    cards = json.loads(CARDS_JSON.read_text(encoding="utf-8"))
    if any(c["deck"] == DECK for c in cards):
        raise SystemExit(f"{DECK} already present — aborting to avoid duplicates")

    total = sum(count for count, _, _ in NEW_ROWS)
    assert total == 60, f"decklist totals {total}, expected 60"

    for count, name, set_ in NEW_ROWS:
        cards.append({"year": YEAR, "deck": DECK, "count": count, "name": name, "set": set_})

    CARDS_JSON.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Added {len(NEW_ROWS)} rows ({total} cards) for {DECK}")


if __name__ == "__main__":
    main()
