"""One-off: replace the old (incorrect) Cinccino Mill (2020) decklist in
data/cards.json with the corrected 60-card list the user supplied.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS_JSON = ROOT / "data" / "cards.json"
DECK = "Cinccino Mill (2020)"

NEW_ROWS = [
    (4, "Minccino", "145/202"),
    (4, "Cinccino", "147/202"),
    (1, "Ditto Prism Star", "154/214"),
    (2, "Zacian V", "138/202"),
    (1, "Magcargo-GX", "44/214"),
    (1, "Mew", "76/214"),
    (2, "Oranguru", "114/156"),
    (1, "Mewtwo & Mew-GX", "71/236"),
    (2, "Lt. Surge's Strategy", "178/214"),
    (4, "Bellelba & Brycen-Man", "186/236"),
    (3, "Cynthia & Caitlin", "189/236"),
    (1, "Faba", "173/214"),
    (1, "Tate & Liza", "148/168"),
    (1, "Evolution Incense", "163/202"),
    (4, "Quick Ball", "179/202"),
    (2, "Air Balloon", "156/202"),
    (1, "Pokémon Communication", "152/181"),
    (3, "Tag Call", "206/236"),
    (2, "Ordinary Rod", "171/202"),
    (4, "Lillie's Poké Doll", "197/236"),
    (4, "Pal Pad", "132/156"),
    (4, "Great Ball", "119/149"),
    (4, "Crushing Hammer", "115/149"),
    (1, "Recycle Energy", "212/236"),
    (3, "Fire Energy", ""),
]


def main():
    cards = json.loads(CARDS_JSON.read_text(encoding="utf-8"))
    kept = [c for c in cards if c["deck"] != DECK]
    removed = len(cards) - len(kept)

    new_cards = [{"year": "2020", "deck": DECK, "count": count, "name": name, "set": set_}
                 for count, name, set_ in NEW_ROWS]

    total = sum(c["count"] for c in new_cards)
    assert total == 60, f"new decklist totals {total}, expected 60"

    kept.extend(new_cards)
    CARDS_JSON.write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Removed {removed} old rows, added {len(new_cards)} new rows ({total} cards) for {DECK}")


if __name__ == "__main__":
    main()
