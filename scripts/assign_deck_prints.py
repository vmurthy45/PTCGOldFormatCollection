"""Record a verified decklist: exactly which print/version sits in which deck.

Vig checks a physical deck box and reports its 60 cards as
(name, set, number, version, qty). This rewrites the inventory so that deck's
claim matches, WITHOUT inventing or losing copies:

  * every copy that deck currently claims is released back to Spare first
    (and loses its tick -- a released copy is unverified stock again);
  * each reported stack is then filled from stock already owned, preferring
    (1) the same print + version, (2) the same print any version, (3) a
    "set unknown" row of that card (this is the normal case — telling me the
    print of copies I only knew by name), (4) any other print's spare;
  * only if the card genuinely isn't in stock are new copies added, and that
    is reported so it can be sanity-checked.

Import and call assign(inventory, deck, stacks); it returns a report dict.
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "inventory.json"


def name_key(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace("’", "'")
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"^basic\s+", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def _rows(inv, key):
    return [e for e in inv if e["key"] == key]


def _take(row, qty, version=None):
    """Pull up to qty spare copies out of a row; returns how many were taken."""
    got = 0
    out = []
    for v in row["variants"]:
        if got < qty and v["source"] == "Spare" and (version is None or v["version"] == version):
            take = min(qty - got, v["qty"])
            got += take
            if v["qty"] - take > 0:
                out.append({**v, "qty": v["qty"] - take})
        else:
            out.append(v)
    row["variants"] = out
    row["total"] = sum(v["qty"] for v in out)
    return got


def assign(inv, deck, stacks, image_for=None):
    keys = {name_key(n) for n, *_ in stacks}

    # 1) release this deck's existing claim on every card it mentions
    for e in inv:
        if e["key"] in keys:
            e["variants"] = [({**v, "source": "Spare", "verified": False}
                              if v["source"] == deck else v)
                             for v in e["variants"]]
            e["total"] = sum(v["qty"] for v in e["variants"])

    report = {"created_rows": [], "new_copies": [], "moved": 0}

    for name, s, num, version, qty in stacks:
        k = name_key(name)
        rows = _rows(inv, k)
        target = next((e for e in rows if e["set"] == s and e["num"] == num), None)
        if target is None:
            src = rows[0] if rows else None
            target = {"name": name, "type": (src or {}).get("type", ""), "key": k,
                      "set": s, "num": num, "printKey": f"{k}|{s} {num}",
                      "image": (image_for or {}).get((s, num)), "total": 0, "variants": []}
            inv.append(target)
            rows.append(target)
            report["created_rows"].append(f"{name} {s} {num}")

        need = qty
        # (1) this print, same version  (2) this print, any version
        for ver in (version, None):
            if need <= 0:
                break
            need -= _take(target, need, ver)
        # (3) a set-unknown row of this card, then (4) any other print
        for pref_unknown in (True, False):
            for e in rows:
                if need <= 0:
                    break
                if e is target or (pref_unknown and e["set"]):
                    continue
                for ver in (version, None):
                    if need <= 0:
                        break
                    moved = _take(e, need, ver)
                    need -= moved
                    report["moved"] += moved
        if need > 0:
            report["new_copies"].append(f"{need}x {name} {s} {num} ({version})")

        target["variants"].insert(0, {"version": version, "qty": qty,
                                      "source": deck, "verified": True})
        target["total"] = sum(v["qty"] for v in target["variants"])

    # Verification is per stack: this box has been checked, so only its own
    # stacks are ticked. Other decks sharing the same print row are untouched --
    # a row-level flag used to clear their checklists for them.
    inv[:] = [e for e in inv if e["total"] > 0]
    inv.sort(key=lambda e: (e["name"].lower(), e["set"] == "", e["set"], e["num"]))
    return report


def load():
    return json.loads(INV.read_text(encoding="utf-8"))


def save(inv):
    INV.write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")
