"""Move verification from the inventory ROW onto each individual stack.

The old flag sat on the row (one print of one card), but a row is shared: Iono
PAL 185 is held by nine different decks. Marking it verified because one box was
checked said nothing about the other eight, and checking a box silently cleared
other decks' checklists. Verification is really a fact about *a deck's copies of
a print* -- exactly what a variant is -- so the flag belongs there:

    {"version": "World Champs", "qty": 4, "source": "Dragapult (2025)",
     "verified": true}

A row's status is then derived: all stacks verified, some, or none.

Seeded from the boxes Vig has physically opened (2025 and 2026). Everything else
starts unverified, including Spare stacks and the rows the old auto-verify pass
had flagged -- those were deductions from the print rules Vig gave by year, not
cards anyone has looked at. The verified count drops as a result; it is now
counting something stricter.

    .venv/bin/python scripts/migrate_verification.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "inventory.json"
CARDS = ROOT / "data" / "cards.json"

# the years whose boxes have been checked card by card
CHECKED_YEARS = {"2025", "2026"}


def main():
    inv = json.loads(INV.read_text(encoding="utf-8"))
    cards = json.loads(CARDS.read_text(encoding="utf-8"))
    checked = {c["deck"] for c in cards if str(c.get("year")) in CHECKED_YEARS}

    stacks = done = 0
    for e in inv:
        e.pop("verified", None)             # row-level flag is gone
        for v in e["variants"]:
            stacks += 1
            if v.get("source") in checked:
                v["verified"] = True
                done += 1
            else:
                v.pop("verified", None)

    INV.write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(inv)} rows, {stacks} stacks; {done} verified "
          f"({len(checked)} decks physically checked).")


if __name__ == "__main__":
    main()
