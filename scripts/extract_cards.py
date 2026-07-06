"""One-off: pull the CARDS JSON blob out of the v1 index.html and save it as data/cards.json."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "index.v1.html"
OUT = ROOT / "data" / "cards.json"

text = SRC.read_text(encoding="utf-8")
m = re.search(r'<script id="data" type="application/json">(.*?)</script>', text, re.S)
if not m:
    raise SystemExit("Could not find #data script block in index.v1.html")

cards = json.loads(m.group(1))
OUT.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {len(cards)} card rows across {len(set(c['deck'] for c in cards))} decks to {OUT}")
