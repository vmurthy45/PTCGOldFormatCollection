"""Make each deck line show the print that deck actually mostly holds.

A decklist carries ONE row per card name (Vig's preference — the list reads
tidily). When a verified box turns out to hold two printings of the same card,
that row should display the majority one: 3 Great Ball SLG 60 + 1 SUM 119 shows
as SLG 60. The split itself stays in data/inventory.json as separate stacks.

Only runs against decks where every stack is verified — an unverified deck's
inventory is still inference, so it has no authority over the list.

Card names that appear on TWO rows of one deck are skipped: those are different
cards sharing a name (Garbodor GRI 51 Trashalanche vs BKP 57 Garbotoxin), not
reprints, and each row keeps its own print.

    .venv/bin/python scripts/align_deck_prints.py          # report
    .venv/bin/python scripts/align_deck_prints.py --fix    # apply
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

# Basic energy keeps an empty `set` in a decklist, which is also what
# merge_image_urls.py keys its URL_OVERRIDES on -- give one a real set number
# and that script deletes its image on the next run. The print lives in the
# inventory instead.
BASIC = {"lightningenergy", "darknessenergy", "fireenergy", "grassenergy",
         "psychicenergy", "waterenergy", "fightingenergy", "metalenergy",
         "fairyenergy"}
# Japanese-only sets. A decklist names the English print it stands in for, as
# every M2a row in the data already does; only the inventory records the card.
JAPANESE = {"M2a", "M3", "MEP", "s12a"}


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


def main():
    fix = "--fix" in sys.argv
    inv = json.loads(INV.read_text(encoding="utf-8"))
    cards = json.loads(CARDS.read_text(encoding="utf-8"))

    sys.path.insert(0, str(ROOT / "scripts"))
    from build_inventory import CODE_TO_ID, SCRYDEX_IDS, card_number
    id_to_code = {v: k for k, v in CODE_TO_ID.items()}

    # printed totals, learned from rows already in the data
    totals = {}
    for c in cards:
        sid = set_id_of(c.get("image"))
        st = str(c.get("set") or "")
        if sid and "/" in st:
            totals.setdefault(sid, st.split("/", 1)[1])

    def image_for(code, num):
        sid = CODE_TO_ID.get(code)
        if not sid or not num:
            return None, None
        n = card_number(num, sid)
        url = (f"https://images.scrydex.com/pokemon/{sid}-{n}/large"
               if sid in SCRYDEX_IDS else f"https://images.pokemontcg.io/{sid}/{n}_hires.png")
        return url, totals.get(sid)

    # which decks are fully verified
    stacks_by_deck = defaultdict(list)
    for e in inv:
        for v in e["variants"]:
            src = v.get("source")
            if src and src != "Spare":
                stacks_by_deck[src].append((e, v))
    verified = {d for d, sv in stacks_by_deck.items() if all(v.get("verified") for _, v in sv)}

    rows_by = defaultdict(list)
    for c in cards:
        rows_by[(c["deck"], c["name"])].append(c)

    changed, skipped = [], []
    for deck in sorted(verified):
        held = defaultdict(lambda: defaultdict(int))     # key -> (set,num) -> qty
        for e, v in stacks_by_deck[deck]:
            held[e["key"]][(e.get("set", ""), e.get("num", ""))] += v["qty"]
        for (d, name), rows in rows_by.items():
            if d != deck:
                continue
            key = name_key(name)
            if key in BASIC:
                continue
            prints = held.get(key)
            if not prints:
                continue
            prints = {k: v for k, v in prints.items() if k[0] not in JAPANESE}
            if not prints:
                continue
            if len(rows) > 1:
                if len(prints) > 1:
                    skipped.append(f"{deck}: {name} — {len(rows)} deck rows, left alone")
                continue
            c = rows[0]
            top = max(prints.items(), key=lambda kv: kv[1])
            (code, num), qty = top
            if not code or not num:
                continue                      # basics and unresolved prints
            cur_code = id_to_code.get(set_id_of(c.get("image")))
            cur_num = str(c.get("set") or "").split("/")[0]
            if (cur_code, cur_num) == (code, num):
                continue
            if sum(prints.values()) == qty:
                why = "the deck's only print"
            elif qty * 2 == sum(prints.values()):
                continue                      # a tie has no majority; leave it
            else:
                why = f"{qty} of {sum(prints.values())}"
            url, tot = image_for(code, num)
            if not url or not tot:
                skipped.append(f"{deck}: {name} — cannot build a {code} {num} image/total")
                continue
            changed.append((deck, name, f"{cur_code} {cur_num}", f"{code} {num}", why))
            if fix:
                c["set"] = f"{num}/{tot}"
                c["image"] = url

    if fix and changed:
        CARDS.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(verified)} decks fully verified")
    for deck, name, was, now, why in changed:
        print(f"  {deck:<28} {name:<26} {was:<12} -> {now:<12} ({why})")
    for s in skipped:
        print(f"  note: {s}")
    print(f"\n{len(changed)} deck lines {'updated' if fix else 'to update'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
