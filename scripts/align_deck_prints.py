"""Make each deck line match the box: its print, and its print TYPE.

Two passes, both only over fully verified decks.

1. the print shown on the row (set number + image) — the majority one the box
   actually holds;
2. the row's `prints{authentic, wc, proxy}`, which drives the coloured pips in
   the expanded deck view. A stack's inventory version says which bucket it
   belongs in: "World Champs" -> wc, "Proxy" -> proxy, and every other version
   (Standard, Holo, Reverse Holo, Prize Pack, Japanese, Full Art) is a retail
   copy -> authentic. Missing stays whatever `count` minus the owned buckets
   leaves, so it is never touched directly.

A decklist carries ONE row per card name (Vig's preference — the list reads
tidily). When a verified box turns out to hold two printings of the same card,
that row should display the majority one: 3 Great Ball SLG 60 + 1 SUM 119 shows
as SLG 60. The split itself stays in data/inventory.json as separate stacks.

Gated per CARD, not per deck: a line is only touched when every stack of that
card in that deck is verified. A deck part-way through checking still gets its
confirmed lines updated, and one outstanding energy no longer holds back the
other twenty-two.

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

# Basic energy is included now that Vig identifies the print box by box. It
# only lands on a decklist when the inventory row has BOTH a set and a card
# number: the 'XY' placeholder row (set, no number) means "print not identified
# yet", and SWSH-era energies are printed without a number at all, so both fall
# through the same `not num` guard below and stay off the list.
# Japanese-only sets. A decklist names the English print it stands in for, as
# every M2a row in the data already does; only the inventory records the card.
JAPANESE = {"M2a", "M3", "MEP", "s12a"}
# Printed totals for sets no deck row uses yet, so a first-of-its-kind print can
# still be written onto a decklist. BWTK is the Black & White Trainer Kit, which
# the card API does not catalogue at all -- its rows carry a hand-set image.
EXTRA_TOTALS = {"col1": "95", "ecard1": "165", "base1": "102",
                "gym1": "132", "gym2": "132", "det1": "18", "dp1": "130"}
NO_API = {"BWTK"}
# Rows where Vig has fixed what the decklist shows, overriding the majority
# rule. ToadBats plays a Zubat PLS 53 with a SUM 54 standing in for it, and a
# Computer Search he wants pictured as BCR 137 while the card in the sleeve is
# Base Set 71 -- in both the list and the inventory are deliberately different.
PINNED = {("ToadBats (2015)", "Zubat"),
          ("ToadBats (2015)", "Computer Search"),
          # a BKT 97 sits in the sleeve; Vig wants the list to keep showing the
          # PLF 47 that is the right card for this deck
          ("Darkrai (2013)", "Mr. Mime"),
          # same shape as ToadBats: a Base Set 71 stands in, pictured as BCR 137.
          # Unlike ToadBats, Vig asked for this one's pip to read proxy.
          ("Yveltal Raichu (2014)", "Computer Search")}


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

    stacks_by_deck = defaultdict(list)
    for e in inv:
        for v in e["variants"]:
            src = v.get("source")
            if src and src != "Spare":
                stacks_by_deck[src].append((e, v))
    # (deck, card key) -> every stack of that card is confirmed
    card_ok = defaultdict(lambda: True)
    for d, sv in stacks_by_deck.items():
        for e, v in sv:
            if not v.get("verified"):
                card_ok[(d, e["key"])] = False
            else:
                card_ok.setdefault((d, e["key"]), True)
    verified = sorted(stacks_by_deck)

    rows_by = defaultdict(list)
    for c in cards:
        rows_by[(c["deck"], c["name"])].append(c)

    changed, merge, ask, unresolved = [], [], [], []
    for deck in verified:
        held = defaultdict(lambda: defaultdict(int))     # key -> (set,num) -> qty
        for e, v in stacks_by_deck[deck]:
            held[e["key"]][(e.get("set", ""), e.get("num", ""))] += v["qty"]
        for (d, name), rows in rows_by.items():
            if d != deck:
                continue
            if (deck, name) in PINNED or not card_ok.get((deck, name_key(name))):
                continue
            prints = held.get(name_key(name))
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
            cur_code_pre = id_to_code.get(set_id_of(c.get("image")))
            # 'XY' with no number is the merge script's placeholder for "a basic
            # energy whose printing was never recorded" -- NOT a claim that the
            # card is from XY base. It must never reach a decklist.
            if code == "XY" and not num:
                continue
            if code and not num:
                # SWSH-era basic energies are printed with a set symbol but no
                # collector number, so the set code alone is the whole answer.
                # Vig asked for these to read just "SSH". The card API has no
                # image for them, so the row keeps the energy art it already has.
                if c.get("set") != code:
                    changed.append((deck, name, c.get("set") or "(none)", code,
                                    "set only, this print has no card number"))
                    if fix:
                        c["set"] = code
                continue
            if not code or not num:
                continue                      # print still unidentified
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

    # ---- pass 2: print type, so the pips match the box --------------------
    WC, PROXY = "World Champs", "Proxy"
    pips = []
    for deck in verified:
        owned = defaultdict(lambda: {"authentic": 0, "wc": 0, "proxy": 0})
        for e, v in stacks_by_deck[deck]:
            bucket = "wc" if v["version"] == WC else ("proxy" if v["version"] == PROXY
                                                      else "authentic")
            owned[e["key"]][bucket] += v["qty"]
        for (d, name), rows in rows_by.items():
            if d != deck or len(rows) > 1:
                continue
            c = rows[0]
            if not card_ok.get((deck, name_key(name))):
                continue
            got = owned.get(name_key(name))
            if not got:
                continue
            cur = {f: (c.get("prints") or {}).get(f, 0) for f in ("authentic", "wc", "proxy")}
            # Proxy is a fact about the DECK, not the card: Alakazam plays two
            # ordinary Dunsparce PAL 156 as stand-ins, so the inventory calls
            # them Standard while the deck row rightly says proxy. Never demote
            # an existing proxy count -- only ever raise it.
            got["proxy"] = max(got["proxy"], cur["proxy"])
            owned_total = sum(v["qty"] for e, v in stacks_by_deck[deck]
                              if e["key"] == name_key(name))
            got["authentic"] = max(0, owned_total - got["wc"] - got["proxy"])
            if cur == got:
                continue
            # never let this invent copies the deck does not own
            if sum(got.values()) > c["count"]:
                unresolved.append(f"{deck}: {name} — inventory holds "
                                  f"{sum(got.values())} but the deck plays {c['count']}")
                continue
            pips.append((deck, name, cur, got))
            if fix:
                c["prints"] = dict(got)

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

    if fix and (changed or pips):
        CARDS.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{sum(1 for k, ok in card_ok.items() if ok)} verified card lines "
          f"across {len(verified)} decks")
    for deck, name, was, now, why in changed:
        print(f"  {deck:<28} {name:<26} {was:<12} -> {now:<12} ({why})")
    for deck, name, cur, got in pips:
        f = lambda p: "/".join(str(p[k]) for k in ("authentic", "wc", "proxy"))
        print(f"  pips  {deck:<28} {name:<26} {f(cur):<10} -> {f(got)}")
    for a in ask:
        print(f"  Pokémon duplicate, left split (say if you want it merged): {a}")
    for u in unresolved:
        print(f"  could not update: {u}")
    print(f"\n{len(changed)} deck lines and {len(pips)} pip rows "
          f"{'updated' if fix else 'to update'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
