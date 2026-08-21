"""One-off migration: make each PRINT of a card its own inventory entry.

Azelf LA 19 and Azelf MT 4 are different cards (different art), so they must be
separate rows, not variants stacked under one "Azelf". Print *type* is a
different axis: World Champs / Authentic / Proxy copies of the SAME print stay
together in one entry's `variants`, each naming the deck holding them.

Copies with no set recorded stay lumped in a single "set unknown" entry per
card, pending Vig's physical check.

Entry shape after this runs:
    {name, type, key, set, num, printKey, image, total, verified?, variants[]}
    variants[] = {version, qty, source}
`key` stays the name-match key (used to find deck usage); `printKey` is unique.
"""
import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "inventory.json"


def main():
    inv = json.loads(INV.read_text(encoding="utf-8"))
    if inv and "printKey" in inv[0]:
        print("Already split by print — nothing to do.")
        return

    out = OrderedDict()
    for g in inv:
        for v in g.get("variants", []):
            s, n = str(v.get("set") or ""), str(v.get("num") or "")
            pk = f"{g['key']}|{s} {n}".strip()
            e = out.get(pk)
            if e is None:
                e = out[pk] = {
                    "name": g["name"], "type": g.get("type", ""), "key": g["key"],
                    "set": s, "num": n, "printKey": pk,
                    "image": v.get("image") or g.get("image"),
                    "total": 0, "variants": [],
                }
                if g.get("verified"):
                    e["verified"] = True
            if not e.get("image") and v.get("image"):
                e["image"] = v["image"]
            e["total"] += int(v.get("qty") or 0)
            e["variants"].append({
                "version": v.get("version", "Standard"),
                "qty": int(v.get("qty") or 0),
                "source": v.get("source", "Sheet"),
            })

    rows = sorted(out.values(), key=lambda e: (e["name"].lower(), e["set"] == "",
                                               e["set"], e["num"]))
    INV.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    names = len({e["key"] for e in rows})
    copies = sum(e["total"] for e in rows)
    print(f"Split {len(inv)} cards into {len(rows)} print entries "
          f"({names} distinct card names, {copies} copies).")
    multi = [k for k in {e["key"] for e in rows}
             if len([e for e in rows if e["key"] == k]) > 1]
    print(f"{len(multi)} cards now occupy more than one row (multiple prints).")


if __name__ == "__main__":
    main()
