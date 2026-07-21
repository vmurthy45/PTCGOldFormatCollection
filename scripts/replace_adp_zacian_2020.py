"""One-off: replace the ADP Zacian (2020) decklist in data/cards.json with the
2020 Limitless Invitational build (1 card off) the user supplied.

Set numbers are the period-correct 2020 printings and were HTTP-verified
against pokemontcg.io. The user's export used a couple of modern reprint
codes (Professor's Research "JTG 155", SVE-style basic energy codes); those
are displayed here as their 2020-era prints (Professor's Research SSH
178/202; basic Energy with blank set → XY base art, matching every other
basic Energy in the collection).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS_JSON = ROOT / "data" / "cards.json"
YEAR = "2020"
DECK = "ADP Zacian (2020)"

NEW_ROWS = [
    # Pokémon (10)
    (3, "Zacian V", "138/202"),
    (2, "Arceus & Dialga & Palkia-GX", "156/236"),
    (2, "Dedenne-GX", "57/214"),
    (1, "Oranguru", "148/202"),
    (1, "Eldegoss V", "19/192"),
    # Trainer (40)
    (4, "Professor's Research", "178/202"),
    (4, "Marnie", "169/202"),
    (2, "Boss's Orders", "154/192"),
    (1, "Mallow & Lana", "198/236"),
    (4, "Quick Ball", "179/202"),
    (4, "Metal Saucer", "170/202"),
    (4, "Order Pad", "131/156"),
    (3, "Acro Bike", "123/168"),
    (3, "Energy Switch", "162/202"),
    (2, "Cherish Ball", "191/236"),
    (2, "Energy Spinner", "170/214"),
    (2, "Switch", "183/202"),
    (1, "Great Catcher", "192/236"),
    (1, "Tool Scrapper", "168/192"),
    (2, "Air Balloon", "156/202"),
    (1, "Metal Frying Pan", "112/131"),
    (1, "Chaotic Swell", "187/236"),
    # Energy (10)
    (8, "Metal Energy", ""),
    (2, "Water Energy", ""),
]


def main():
    cards = json.loads(CARDS_JSON.read_text(encoding="utf-8"))
    kept = [c for c in cards if c["deck"] != DECK]
    removed = len(cards) - len(kept)

    total = sum(count for count, _, _ in NEW_ROWS)
    assert total == 60, f"decklist totals {total}, expected 60"

    for count, name, set_ in NEW_ROWS:
        kept.append({"year": YEAR, "deck": DECK, "count": count, "name": name, "set": set_})

    CARDS_JSON.write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Removed {removed} old rows, added {len(NEW_ROWS)} new rows ({total} cards) for {DECK}")


if __name__ == "__main__":
    main()
