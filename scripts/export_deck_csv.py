"""Flat CSV of every card sleeved in every deck, one row per stack.

A *stack* is one deck's copies of one print at one finish, which is exactly the
granularity Vig verified box by box -- so 3 Standard + 1 Reverse Holo of the
same card come out as two rows, not one.

    Year, Deck, Quantity, Card Name, Set number, Print

Set number reads "XXX 123" (PAL 185, PR-SM SM30). Energies printed without a
collector number show the set code alone (SSH); the handful whose printing is
still unidentified are left blank. Only cards physically in the boxes are
listed -- anything still flagged missing has no stack and does not appear.

    .venv/bin/python scripts/export_deck_csv.py [out.csv]
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORDER = {"Pokemon": 0, "Trainer": 1, "Energy": 2}


def name_key(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace("’", "'")
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"^basic\s+", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "deck_contents.csv"
    inv = json.loads((ROOT / "data" / "inventory.json").read_text(encoding="utf-8"))
    cards = json.loads((ROOT / "data" / "cards.json").read_text(encoding="utf-8"))

    year = {c["deck"]: str(c["year"]) for c in cards}
    # category lives on the deck row, not the inventory row, and is the tidy
    # three-way split; the inventory's `type` breaks Trainers into Item/
    # Supporter/Stadium, which is not what the decklists group by.
    cat = {(c["deck"], name_key(c["name"])): c.get("category", "") for c in cards}

    rows = []
    for e in inv:
        for v in e["variants"]:
            deck = v.get("source")
            if not deck or deck == "Spare":
                continue
            code, num = e.get("set") or "", e.get("num") or ""
            # 'XY' with no card number is the placeholder for "basic energy,
            # printing never recorded" -- NOT a claim the card is XY base. It
            # must not reach the CSV as a real set. Genuine unnumbered prints
            # (SSH, TEU) keep their bare code.
            if code == "XY" and not num:
                code = ""
            setnum = " ".join(x for x in (code, num) if x)
            rows.append({
                "Year": year.get(deck, ""),
                "Deck": deck,
                "Quantity": v["qty"],
                "Card Name": e["name"],
                "Set number": setnum,
                "Print": v["version"],
                "_cat": ORDER.get(cat.get((deck, e["key"]), ""), 9),
            })

    # newest year first, then deck, then Pokémon -> Trainer -> Energy, as the
    # site lists them; card name last so a split card's prints sit together
    rows.sort(key=lambda r: (-int(r["Year"] or 0), r["Deck"].lower(),
                             r["_cat"], r["Card Name"].lower(), r["Set number"]))

    fields = ["Year", "Deck", "Quantity", "Card Name", "Set number", "Print"]
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    copies = sum(r["Quantity"] for r in rows)
    blank = sum(1 for r in rows if not r["Set number"])
    print(f"{out}: {len(rows)} rows · {copies} copies · "
          f"{len({r['Deck'] for r in rows})} decks")
    if blank:
        print(f"  {blank} rows have no set recorded yet (the parked basic-energy backfill)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
