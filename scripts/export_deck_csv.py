"""Flat CSV of every card sleeved in every deck, one row per stack.

A *stack* is one deck's copies of one print at one finish, which is exactly the
granularity Vig verified box by box -- so 3 Standard + 1 Reverse Holo of the
same card come out as two rows, not one.

    Year, Deck, Quantity, Card Name, Set number, Print

With --spare it lists everything still loose or still unidentified: every
Spare stack (Deck reads "Spare", Year is blank) plus any stack a deck holds
whose printing was never recorded. A blank Set number is the tell in both
cases -- that is the "set unknown" state.

With --missing it instead lists the cards each deck is SHORT: quantity is how
many copies are still to find, Print reads "Missing", and the set number is the
print the decklist calls for -- i.e. what to go buy.

Set number reads "XXX 123" (PAL 185, PR-SM SM30). Energies printed without a
collector number show the set code alone (SSH); the handful whose printing is
still unidentified are left blank. Only cards physically in the boxes are
listed -- anything still flagged missing has no stack and does not appear.

    .venv/bin/python scripts/export_deck_csv.py [out.csv]
    .venv/bin/python scripts/export_deck_csv.py --missing [out.csv]
    .venv/bin/python scripts/export_deck_csv.py --spare   [out.csv]
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORDER = {"Pokemon": 0, "Trainer": 1, "Energy": 2}


def write(out, rows):
    fields = ["Year", "Deck", "Quantity", "Card Name", "Set number", "Print"]
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def name_key(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace("’", "'")
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"^basic\s+", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def set_id_of(url):
    m = (re.search(r"pokemontcg\.io/([^/]+)/", url or "")
         or re.search(r"scrydex\.com/pokemon/([a-z0-9]+)-", url or "", re.I))
    return m.group(1) if m else None


def missing_rows(cards):
    """Cards a deck is short. These have no inventory stack -- a missing copy
    is not owned -- so the print comes off the deck row instead."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_inventory import CODE_TO_ID
    id_to_code = {v: k for k, v in CODE_TO_ID.items()}
    out = []
    for c in cards:
        pr = c.get("prints") or {}
        short = c["count"] - sum(pr.values())
        if short <= 0:
            continue
        code = id_to_code.get(set_id_of(c.get("image"))) or ""
        num = str(c.get("set") or "").split("/")[0]
        if code == "XY" and not num:
            code = ""
        out.append({"Year": str(c["year"]), "Deck": c["deck"], "Quantity": short,
                    "Card Name": c["name"],
                    "Set number": " ".join(x for x in (code, num) if x),
                    "Print": "Missing",
                    "_cat": ORDER.get(c.get("category", ""), 9)})
    return out


def spare_rows(inv, year, cat):
    """Loose stock, plus deck stacks whose print is still unknown."""
    out = []
    for e in inv:
        code, num = e.get("set") or "", e.get("num") or ""
        unknown = not code or (code == "XY" and not num)
        for v in e["variants"]:
            src = v.get("source") or ""
            if src != "Spare" and not unknown:
                continue
            out.append({"Year": "" if src == "Spare" else year.get(src, ""),
                        "Deck": src or "Spare", "Quantity": v["qty"],
                        "Card Name": e["name"],
                        "Set number": "" if unknown else " ".join(x for x in (code, num) if x),
                        "Print": v["version"],
                        "_cat": ORDER.get(cat.get((src, e["key"]), ""), 9),
                        "_spare": src == "Spare"})
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    missing = "--missing" in sys.argv
    spare = "--spare" in sys.argv
    out = Path(args[0]) if args else ROOT / (
        "deck_missing.csv" if missing else
        "spare_and_unknown.csv" if spare else "deck_contents.csv")
    inv = json.loads((ROOT / "data" / "inventory.json").read_text(encoding="utf-8"))
    cards = json.loads((ROOT / "data" / "cards.json").read_text(encoding="utf-8"))

    year = {c["deck"]: str(c["year"]) for c in cards}
    # category lives on the deck row, not the inventory row, and is the tidy
    # three-way split; the inventory's `type` breaks Trainers into Item/
    # Supporter/Stadium, which is not what the decklists group by.
    cat = {(c["deck"], name_key(c["name"])): c.get("category", "") for c in cards}

    if spare:
        rows = spare_rows(inv, year, cat)
        # deck-held unknowns first (they belong to a box), loose stock after
        rows.sort(key=lambda r: (r["_spare"], -int(r["Year"] or 0),
                                 r["Deck"].lower(), r["_cat"],
                                 r["Card Name"].lower(), r["Set number"]))
        write(out, rows)
        loose = [r for r in rows if r["_spare"]]
        print(f"{out}: {len(rows)} rows · {sum(r['Quantity'] for r in rows)} copies")
        print(f"  {len(loose)} loose stacks ({sum(r['Quantity'] for r in loose)} copies)")
        print(f"  {len(rows) - len(loose)} deck stacks whose print is still unknown")
        print(f"  {sum(1 for r in rows if not r['Set number'])} rows have no set recorded")
        return 0

    if missing:
        rows = missing_rows(cards)
        rows.sort(key=lambda r: (-int(r["Year"] or 0), r["Deck"].lower(),
                                 r["_cat"], r["Card Name"].lower()))
        write(out, rows)
        print(f"{out}: {len(rows)} rows · "
              f"{sum(r['Quantity'] for r in rows)} copies to find · "
              f"{len({r['Deck'] for r in rows})} decks")
        return 0

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

    write(out, rows)
    copies = sum(r["Quantity"] for r in rows)
    blank = sum(1 for r in rows if not r["Set number"])
    print(f"{out}: {len(rows)} rows · {copies} copies · "
          f"{len({r['Deck'] for r in rows})} decks")
    if blank:
        print(f"  {blank} rows have no set recorded yet (the parked basic-energy backfill)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
