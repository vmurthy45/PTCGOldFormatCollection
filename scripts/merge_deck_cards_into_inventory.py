"""Fold cards from pre-2026 decks into data/inventory.json.

The purchases spreadsheet turned out to be a record of *recent acquisitions*,
not a full count of everything owned: Zacian V showed 1 copy in the sheet while
five 2020-2023 decks were holding 11 more. So the accounting is:

    total owned = sheet copies + copies sleeved in pre-2026 decks
    spare       = sheet copies - copies used by 2026 decks

i.e. pre-2026 deck cards are ALWAYS added on top of the sheet (they were never
counted there), while 2026 decks draw on the sheet stock (those cards were
bought recently and are already in it), so their copies are not added again.

Quantities come from each deck's own print data (authentic + wc + proxy);
missing copies aren't owned, so they aren't counted. One variant per
deck/print-type keeps the provenance visible for Vig's later verification pass.

Run after build_inventory.py, which re-seeds the sheet half:
    .venv/bin/python scripts/build_inventory.py
    .venv/bin/python scripts/merge_deck_cards_into_inventory.py
"""
import json
import re
import sys
import unicodedata
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "inventory.json"
CARDS = ROOT / "data" / "cards.json"

PRINT_LABEL = {"authentic": "Standard", "wc": "World Champs", "proxy": "Proxy"}
CAT_TYPE = {"Pokemon": "Pokémon", "Trainer": "Trainer", "Energy": "Energy"}


def name_key(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace("’", "'")
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"^basic\s+", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def set_code_from_image(url, code_by_id):
    """Deck rows store the set as 'num/printedTotal'; the actual set lives in
    the image URL. Recover the PTCGO code so it displays like sheet entries."""
    if not url:
        return ""
    m = (re.search(r"images\.pokemontcg\.io/([^/]+)/", url)
         or re.search(r"scrydex\.com/pokemon/([a-z0-9]+)-", url, re.I))
    return code_by_id.get(m.group(1), "") if m else ""


def main():
    year_max = 2026
    for i, a in enumerate(sys.argv):
        if a == "--year-max" and i + 1 < len(sys.argv):
            year_max = int(sys.argv[i + 1])

    sys.path.insert(0, str(ROOT / "scripts"))
    from build_inventory import CODE_TO_ID
    code_by_id = {v: k for k, v in CODE_TO_ID.items()}

    cards = json.loads(CARDS.read_text(encoding="utf-8"))
    inventory = json.loads(INV.read_text(encoding="utf-8"))

    # drop any previously merged deck variants so this is safe to re-run
    for g in inventory:
        g["variants"] = [v for v in g.get("variants", [])
                         if not v.get("source") or v["source"] == "Spare"]
    by_key = {g["key"]: g for g in inventory if g["variants"]}

    added_cards = added_copies = 0
    for c in cards:
        try:
            year = int(str(c.get("year", ""))[:4])
        except ValueError:
            continue
        if year >= year_max:
            continue                      # 2026 decks draw on the sheet stock
        k = name_key(c["name"])
        prints = c.get("prints") or {}
        num = str(c.get("set") or "").split("/")[0]
        code = set_code_from_image(c.get("image"), code_by_id)
        g = by_key.get(k)
        if g is None:
            g = {"name": c["name"],
                 "type": CAT_TYPE.get(c.get("category"), c.get("category", "")),
                 "key": k, "total": 0, "variants": []}
            by_key[k] = g
            added_cards += 1
        for field, label in PRINT_LABEL.items():
            qty = int(prints.get(field, 0) or 0)
            if qty <= 0:
                continue
            added_copies += qty
            g["variants"].append({
                "version": label, "set": code, "num": num, "qty": qty,
                "image": c.get("image"), "source": c["deck"],
            })

    out = sorted(by_key.values(), key=lambda g: g["name"].lower())
    for g in out:
        g["total"] = sum(v["qty"] for v in g["variants"])
    INV.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(g["total"] for g in out)
    sheet = sum(v["qty"] for g in out for v in g["variants"]
                if (v.get("source") or "Spare") == "Spare")
    print(f"Added {added_copies} copies from pre-{year_max} decks "
          f"({added_cards} cards new to the inventory).")
    print(f"Inventory: {len(out)} cards, {total} copies "
          f"({sheet} loose + {total - sheet} sleeved in decks).")


if __name__ == "__main__":
    main()
