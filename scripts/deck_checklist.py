"""Print what still needs confirming for one deck box.

Covers BOTH gaps: cards the inventory already claims for this deck but hasn't
verified, AND cards the deck needs that the inventory doesn't attribute to it at
all (shared staples, whose copies are only inferred at display time). Cards
flagged missing for the deck are listed separately so they're never reported as
physically present.

    --copy   paste-back format: "Nx Card Name = " for Vig to fill in
    --all    every card in the box, not just the unconfirmed ones, with the
             set code the decklist expects pre-filled so most lines are a
             yes/no rather than something to write out
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def key(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace("’", "'")
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"^basic\s+", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


ID_TO_CODE = None


def set_code(c):
    """The set the decklist says this card comes from: 'PAL 185', or 'basic'."""
    global ID_TO_CODE
    if ID_TO_CODE is None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_inventory import CODE_TO_ID
        ID_TO_CODE = {v: k for k, v in CODE_TO_ID.items()}
    url = c.get("image") or ""
    m = (re.search(r"pokemontcg\.io/([^/]+)/", url)
         or re.search(r"scrydex\.com/pokemon/([a-z0-9]+)-", url, re.I))
    num = str(c.get("set") or "").split("/")[0]
    return f"{ID_TO_CODE.get(m.group(1), '?')} {num}".strip() if m and num else "basic"


def main():
    deck = sys.argv[1]
    inv = json.loads((ROOT / "data/inventory.json").read_text(encoding="utf-8"))
    cards = json.loads((ROOT / "data/cards.json").read_text(encoding="utf-8"))
    rows = [c for c in cards if c["deck"] == deck]
    if not rows:
        sys.exit(f"no such deck: {deck}")

    claim = defaultdict(int)
    verified = {}
    by_key = defaultdict(list)
    for e in inv:
        by_key[e["key"]].append(e)
        for v in e["variants"]:
            if v["source"] == deck:
                claim[e["key"]] += v["qty"]
                # per-stack now: only THIS deck's copies count as checked, so a
                # staple confirmed in another box still shows up here
                if not v.get("verified"):
                    verified[e["key"]] = False
                elif e["key"] not in verified:
                    verified[e["key"]] = True

    every = "--all" in sys.argv
    missing, todo = [], []
    for c in sorted(rows, key=lambda c: (c["category"], c["name"])):
        k = key(c["name"])
        m = c["count"] - sum((c.get("prints") or {}).values())
        if m:
            missing.append(f"{m}x {c['name']}")
        have = claim.get(k, 0)
        need = c["count"] - m
        if need == 0:          # wholly missing card: nothing physical to confirm
            continue
        if every or need > have or not verified.get(k):
            known = [f"{v['qty']} {v['version']}" for e in by_key.get(k, [])
                     for v in e["variants"] if v["source"] == deck]
            todo.append((need, c["name"], c["set"], known, need - have, c))

    if "--copy" in sys.argv:
        # paste-back format: Vig appends the print after the "=" and returns it
        print(deck)
        if missing:
            print("# missing, not in the box: " + ", ".join(missing))
        for need, name, st, known, gap, c in todo:
            print(f"{need}x {name} = {set_code(c) if every else ''}".rstrip())
        return
    print(f"{deck}: {sum(c['count'] for c in rows)} cards")
    if missing:
        print("  missing, do NOT list: " + ", ".join(missing))
    print(f"\n{len(todo)} card lines to confirm:\n")
    for need, name, st, known, gap, c in todo:
        note = "no print recorded yet" if gap == need else (
            f"have {', '.join(known)}" + (f"; {gap} unaccounted" if gap else ""))
        print(f"  {need}x {name:<30} deck list {st or 'basic':<10} ({note})")


if __name__ == "__main__":
    main()
