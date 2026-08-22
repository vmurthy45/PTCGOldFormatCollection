"""Health check for data/inventory.json. Run after EVERY change to it.

Each check here exists because the thing it looks for actually went wrong once:
row totals drifting from their variants, the sheet writing "58/202" as a card
number and splitting a print in two, images pointing at the wrong set, a deck
claiming more copies than it plays. Catching them at write time is the whole
point -- most were only found because Vig noticed something odd on the site.

    .venv/bin/python scripts/audit_inventory.py          # report
    .venv/bin/python scripts/audit_inventory.py --fix    # repair what is safe

Exits non-zero if anything is left unresolved, so it can gate a commit.
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "inventory.json"
CARDS = ROOT / "data" / "cards.json"

BASIC = {"lightningenergy", "darknessenergy", "fireenergy", "grassenergy",
         "psychicenergy", "waterenergy", "fightingenergy", "metalenergy",
         "fairyenergy"}


def name_key(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace("’", "'")
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"^basic\s+", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def main():
    fix = "--fix" in sys.argv
    inv = json.loads(INV.read_text(encoding="utf-8"))
    cards = json.loads(CARDS.read_text(encoding="utf-8"))
    decks = {c["deck"] for c in cards}
    issues, fixed = [], []

    sys.path.insert(0, str(ROOT / "scripts"))
    from build_inventory import CODE_TO_ID, SCRYDEX_IDS, card_number

    def image_for(code, num):
        if not code or code not in CODE_TO_ID or not num:
            return None
        sid = CODE_TO_ID[code]
        n = card_number(num, sid)
        return (f"https://images.scrydex.com/pokemon/{sid}-{n}/large"
                if sid in SCRYDEX_IDS
                else f"https://images.pokemontcg.io/{sid}/{n}_hires.png")

    # ---- per row -------------------------------------------------------
    by_print = defaultdict(list)
    for e in inv:
        label = f"{e['name']} {e.get('set','')} {e.get('num','')}".strip()
        by_print[(e["key"], e.get("set", ""), e.get("num", ""))].append(e)

        total = sum(v.get("qty", 0) for v in e["variants"])
        if e.get("total") != total:
            if fix:
                e["total"] = total; fixed.append(f"total corrected on {label}")
            else:
                issues.append(f"{label}: total says {e.get('total')}, variants sum to {total}")

        if e["name"].lower().startswith("basic "):
            if fix:
                e["name"] = re.sub(r"^Basic\s+", "", e["name"])
                fixed.append(f"dropped the \"Basic\" qualifier from {e['name']}")
            else:
                issues.append(f"{label}: energy names do not carry a \"Basic\" qualifier")

        if "/" in str(e.get("num") or ""):
            issues.append(f"{label}: card number still carries the printed total")

        # basics deliberately sit on an 'XY' placeholder row with no number:
        # Vig does not track which basic energy print is in which older deck
        placeholder = e["key"] in BASIC and not e.get("num")
        if e.get("set") and not e.get("num") and not placeholder:
            issues.append(f"{label}: has a set code but no number")

        if e.get("set") in {"M2a", "M3", "MEP", "s12a"} and not e.get("image"):
            issues.append(f"{label}: Japanese print with no English stand-in image")

        if not e.get("image"):
            url = image_for(e.get("set"), e.get("num"))
            if url and fix:
                e["image"] = url; fixed.append(f"image filled in for {label}")
            elif url:
                issues.append(f"{label}: no image, but one can be derived")

        want = f"{e['key']}|{(e.get('set','') + ' ' + e.get('num','')).strip()}"
        if e.get("printKey") != want:
            if fix:
                e["printKey"] = want; fixed.append(f"printKey corrected on {label}")
            else:
                issues.append(f"{label}: printKey is {e.get('printKey')!r}, expected {want!r}")

        seen = {}
        merged = []
        for v in e["variants"]:
            if not v.get("version"):
                issues.append(f"{label}: a stack has no version")
            if v.get("source") and v["source"] != "Spare" and v["source"] not in decks:
                issues.append(f"{label}: stack sourced to unknown deck {v['source']!r}")
            k = (v.get("version"), v.get("source"), bool(v.get("verified")))
            if k in seen:
                seen[k]["qty"] += v["qty"]
                (fixed if fix else issues).append(
                    f"{'merged duplicate stack on ' if fix else ''}{label}: "
                    f"{v.get('qty')} {v.get('version')} / {v.get('source')} duplicated")
            else:
                seen[k] = v; merged.append(v)
        if fix:
            e["variants"] = merged
            e["total"] = sum(v["qty"] for v in merged)

        if e["total"] <= 0:
            if fix:
                fixed.append(f"dropped empty row {label}")
            else:
                issues.append(f"{label}: row holds no copies")

    if fix:
        inv = [e for e in inv if e["total"] > 0]

    # ---- one row per print --------------------------------------------
    for (key, s, n), rows in by_print.items():
        if len(rows) > 1:
            issues.append(f"{rows[0]['name']} {s} {n}: {len(rows)} rows for the same print")

    # ---- decks get exactly what they play ------------------------------
    for deck in sorted(decks):
        claim, need = defaultdict(int), defaultdict(int)
        for e in inv:
            for v in e["variants"]:
                if v.get("source") == deck:
                    claim[e["key"]] += v["qty"]
        for c in cards:
            if c["deck"] == deck:
                need[name_key(c["name"])] += sum((c.get("prints") or {}).values())
        for k in set(claim) | set(need):
            if claim.get(k, 0) != need.get(k, 0):
                issues.append(f"{deck}: holds {claim.get(k,0)} of {k}, deck needs {need.get(k,0)}")

    # ---- unresolved prints, worth knowing but not errors ----------------
    unknown = [e for e in inv if not e.get("set") and e["key"] not in BASIC]

    if fix and (fixed or True):
        inv.sort(key=lambda e: (e["name"].lower(), e.get("set", "") == "",
                                e.get("set", ""), e.get("num", "")))
        INV.write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")

    copies = sum(e["total"] for e in inv)
    stacks = sum(len(e["variants"]) for e in inv)
    ok = sum(1 for e in inv for v in e["variants"] if v.get("verified"))
    spare = sum(v["qty"] for e in inv for v in e["variants"] if v.get("source") == "Spare")
    print(f"{len(inv)} rows · {copies} copies · {spare} spare · {ok}/{stacks} stacks verified")
    if unknown:
        print(f"{len(unknown)} rows still have no set recorded "
              f"({sum(e['total'] for e in unknown)} copies) — resolved as boxes get checked")
    for f in fixed:
        print("  fixed:", f)
    for i in issues:
        print("  ISSUE:", i)
    if issues:
        print(f"\n{len(issues)} unresolved. Re-run with --fix for the repairable ones.")
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
