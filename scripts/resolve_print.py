"""Work out which SET a card is from, given only what is printed on it.

Older cards do not carry a set code, but they do carry "127/168" -- the card
number and the set's printed total. Name + number + printed total is almost
always unique, so Vig can report a card the way it actually reads and this
resolves the set code the inventory needs.

    .venv/bin/python scripts/resolve_print.py "Copycat 127/168" "Bill 91/102"
    ... | .venv/bin/python scripts/resolve_print.py        # one per line

Prints the set code to record. When more than one set matches it says so and
lists the candidates rather than guessing -- that is the case to take back to
Vig. A set with no code in CODE_TO_ID is reported too, so it can be added.
"""
import json
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_inventory import CODE_TO_ID

ID_TO_CODE = {v: k for k, v in CODE_TO_ID.items()}
LINE = re.compile(r"^\s*(?:(\d+)\s*x\s+)?(.+?)\s+([A-Za-z0-9]+)\s*/\s*(\d+)\s*$")


def api(query):
    url = "https://api.pokemontcg.io/v2/cards?q=" + urllib.parse.quote(query)
    for _ in range(10):
        p = subprocess.run(["curl", "-s", "--max-time", "30", "-A", "Mozilla/5.0", url],
                           capture_output=True, text=True)
        try:
            return json.loads(p.stdout)["data"]
        except Exception:
            time.sleep(2)
    return None


def resolve(name, num, total):
    hits = api(f'name:"{name}" number:"{num}"')
    if hits is None:
        return None, "api unavailable"
    # the printed total is the discriminator: keep only sets that match it
    match = [c for c in hits if str(c["set"].get("printedTotal")) == str(total)]
    if not match:
        seen = sorted({f"{c['set']['name']} {c['number']}/{c['set'].get('printedTotal')}"
                       for c in hits})
        return None, (f"no set with {total} cards has {name} #{num}"
                      + (f"; that name+number exists in: {', '.join(seen)}" if seen else ""))
    sets = sorted({(c["set"]["id"], c["set"]["name"]) for c in match})
    if len(sets) > 1:
        return None, ("ambiguous: " + ", ".join(f"{n} ({ID_TO_CODE.get(i, i)})" for i, n in sets))
    sid, sname = sets[0]
    code = ID_TO_CODE.get(sid)
    card = match[0]
    if not code:
        return None, f"{sname} has no set code yet — add {sid!r} to CODE_TO_ID"
    return f"{code} {num}", f"{card['name']} — {sname}"


def main():
    args = sys.argv[1:] or [l for l in sys.stdin.read().splitlines() if l.strip()]
    bad = 0
    for raw in args:
        m = LINE.match(raw)
        if not m:
            print(f"  ?? {raw}   (expected 'Name 127/168')"); bad += 1; continue
        qty, name, num, total = m.groups()
        code, note = resolve(name.strip(), num, total)
        pre = f"{qty}x " if qty else ""
        if code:
            print(f"  {pre}{name.strip()} {num}/{total}  ->  {code}      {note}")
        else:
            print(f"  {pre}{name.strip()} {num}/{total}  ->  ??  {note}"); bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
