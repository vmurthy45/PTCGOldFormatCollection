"""Make each deck line show the print that deck actually mostly holds.

A decklist carries ONE row per card name (Vig's preference — the list reads
tidily). When a verified box turns out to hold two printings of the same card,
that row should display the majority one: 3 Great Ball SLG 60 + 1 SUM 119 shows
as SLG 60. The split itself stays in data/inventory.json as separate stacks.

Only runs against decks where every stack is verified — an unverified deck's
inventory is still inference, so it has no authority over the list.

Card names that appear on TWO rows of one deck are handled by category, which
is Vig's rule: a **Trainer or Energy** duplicate is a reprint, so it merges to
one line; a **Pokémon** duplicate is nearly always two genuinely different cards
sharing a name (Garbodor GRI 51 Trashalanche vs BKP 57 Garbotoxin, Inteleon SSH
58 Shady Dealings vs CRE 43 Quick Shooting), so it stays split and is reported
for him to confirm rather than merged.

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
# Printed totals for sets no deck row uses yet, so a first-of-its-kind print can
# still be written onto a decklist. BWTK is the Black & White Trainer Kit, which
# the card API does not catalogue at all -- its rows carry a hand-set image.
EXTRA_TOTALS = {"col1": "95", "ecard1": "165", "base1": "102",
                "gym1": "132", "gym2": "132", "det1": "18"}
NO_API = {"BWTK"}


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
    for sid, tot in EXTRA_TOTALS.items():
        totals.setdefault(sid, tot)

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

    changed, merge, ask, unresolved = [], [], [], []
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
            prints = {k: v for k, v in prints.items()
                      if k[0] not in JAPANESE and k[0] not in NO_API}
            if not prints:
                continue
            if len(rows) > 1:
                if rows[0].get("category") == "Pokemon":
                    ask.append(f"{deck}: {name} — {len(rows)} rows, "
                               + " + ".join(f"{r['count']}x {r['set']}" for r in rows))
                else:
                    merge.append((deck, name, rows))
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
            tied = [k for k, n in prints.items() if n == qty]
            if len(tied) > 1:
                # no majority: keep whatever the row already shows if it is one
                # of the tied prints, else take the first by set/number so the
                # choice is stable instead of flipping on every run
                if (cur_code, cur_num) in tied:
                    continue
                code, num = sorted(tied)[0]
                why = f"tie at {qty}, picked one"
            elif sum(prints.values()) == qty:
                why = "the deck's only print"
            else:
                why = f"{qty} of {sum(prints.values())}"
            url, tot = image_for(code, num)
            if not url or not tot:
                unresolved.append(f"{deck}: {name} — no printed total known for {code} {num}")
                continue
            changed.append((deck, name, f"{cur_code} {cur_num}", f"{code} {num}", why))
            if fix:
                c["set"] = f"{num}/{tot}"
                c["image"] = url

    # Trainer/Energy duplicates collapse to one row carrying the majority print
    for deck, name, rows in merge:
        total = sum(r["count"] for r in rows)
        pr = {f: sum((r.get("prints") or {}).get(f, 0) for r in rows)
              for f in ("authentic", "wc", "proxy")}
        keep = max(rows, key=lambda r: r["count"])
        changed.append((deck, name, " + ".join(f"{r['count']}x {r['set']}" for r in rows),
                        f"{total}x {keep['set']}", "merged, Trainer/Energy"))
        if fix:
            keep["count"], keep["prints"] = total, pr
            for r in rows:
                if r is not keep:
                    cards.remove(r)

    if fix and changed:
        CARDS.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(verified)} decks fully verified")
    for deck, name, was, now, why in changed:
        print(f"  {deck:<28} {name:<26} {was:<12} -> {now:<12} ({why})")
    for a in ask:
        print(f"  Pokémon duplicate, left split (say if you want it merged): {a}")
    for u in unresolved:
        print(f"  could not update: {u}")
    print(f"\n{len(changed)} deck lines {'updated' if fix else 'to update'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
