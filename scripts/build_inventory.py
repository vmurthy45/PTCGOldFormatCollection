"""Seed data/inventory.json from the "Collection" sheet of the PTCG Purchases
Tracker spreadsheet.

This is a ONE-OFF / re-seed importer. After the initial import, inventory.json
is the source of truth and is maintained by hand (from what Vig says in chat),
exactly like cards.json — re-running this OVERWRITES those edits, so only run it
when Vig explicitly wants to re-import from the spreadsheet.

The sheet's columns are: Card Name | Card Type | Set | Card Number | Version |
Quantity | Notes. Rows are one (card, print, version) each; they're grouped by
card name so the site can show a card once with its variants underneath.

Card images are resolved here (not at render time) by mapping the PTCGO set code
to a pokemontcg.io/scrydex set id, so the site needs no API calls. Cards whose
set is unknown (Japanese-only sets, some promos) fall back to any English print
of the same name already used by a deck in cards.json.
"""
import json
import re
import sys
import unicodedata
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "inventory.json"
CARDS = ROOT / "data" / "cards.json"
DEFAULT_XLSX = ("/Users/vighnesh/Library/CloudStorage/OneDrive-Personal/"
                "01. Documents/05. Games & Books/TCG/PTCG Purchases Tracker.xlsx")

# PTCGO set code -> pokemontcg.io set id (mirrors SET_CODES in index.html).
CODE_TO_ID = {
    "FO":"base3","BLW":"bw1","PLB":"bw10","LTR":"bw11","EPO":"bw2","NVI":"bw3","NXD":"bw4",
    "DEX":"bw5","DRX":"bw6","BCR":"bw7","PLS":"bw8","PLF":"bw9","PR-BLW":"bwp","CEL":"cel25",
    "DP":"dp1","MT":"dp2","SW":"dp3","GE":"dp4","MD":"dp5","LA":"dp6","SF":"dp7","DRV":"dv1",
    "RS":"ex1","DS":"ex11","LM":"ex12","DF":"ex15","MA":"ex4","TRR":"ex7","GEN":"g1",
    "GH":"gym1","GC":"gym2",
    "HS":"hgss1","UL":"hgss2","UD":"hgss3","TM":"hgss4","MEG":"me1","PFL":"me2","ASC":"me2pt5",
    "POR":"me3","CRI":"me4","PBL":"me5","PGO":"pgo","PL":"pl1","RR":"pl2","SV":"pl3","AR":"pl4",
    "WHT":"rsv10pt5","SUM":"sm1","UNB":"sm10","UNM":"sm11","CEC":"sm12","GRI":"sm2","BUS":"sm3",
    "SLG":"sm35","CIN":"sm4","UPR":"sm5","FLI":"sm6","CES":"sm7","DRM":"sm75","LOT":"sm8",
    "TEU":"sm9","PR-SM":"smp","SVI":"sv1","DRI":"sv10","PAL":"sv2","OBF":"sv3","MEW":"sv3pt5",
    "PAR":"sv4","PAF":"sv4pt5","TEF":"sv5","TWM":"sv6","SFA":"sv6pt5","SCR":"sv7","SSP":"sv8",
    "PRE":"sv8pt5","JTG":"sv9","SSH":"swsh1","ASR":"swsh10","LOR":"swsh11","SIT":"swsh12",
    "CRZ":"swsh12pt5","RCL":"swsh2","DAA":"swsh3","CPA":"swsh35","VIV":"swsh4","BST":"swsh5",
    "CRE":"swsh6","EVS":"swsh7","FST":"swsh8","BRS":"swsh9","PR-SW":"swshp","SWSH":"swshp",
    "XY":"xy1","FCO":"xy10","STS":"xy11","EVO":"xy12","FLF":"xy2","FFI":"xy3","PHF":"xy4",
    "PRC":"xy5","ROS":"xy6","AOR":"xy7","BKT":"xy8","BKP":"xy9","PR-XY":"xyp","BLK":"zsv10pt5",
}
# Mega-era sets pokemontcg.io doesn't host; scrydex does.
SCRYDEX_IDS = {"me2pt5", "me3", "me4", "me5"}


def name_key(s: str) -> str:
    """Match key: accent/case/punctuation-insensitive, ignores variant tags in
    parentheses and a leading 'Basic ' on energy, so 'Tapu Lele GX',
    'Tapu Lele-GX' and 'Basic Metal Energy' land on their deck counterparts."""
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace("’", "'")
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"^basic\s+", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


# Promo set ids number their cards with a prefix (SWSH107, SM30, XY184, BW28).
PROMO_PREFIX = {"swshp": "SWSH", "smp": "SM", "xyp": "XY", "bwp": "BW"}


def card_number(num, sid):
    """Normalise a sheet 'Card Number' into the number the image host uses:
    '45/113' -> '45', '087' -> '87', and promos get their set prefix."""
    n = str(num).strip().split("/")[0].strip()
    if re.fullmatch(r"0\d+", n):          # leading zeros: 087 -> 87
        n = str(int(n))
    prefix = PROMO_PREFIX.get(sid)
    if prefix and not n.upper().startswith(prefix):
        if sid == "swshp" and n.isdigit():   # SWSH promos are zero-padded: SWSH018
            n = n.zfill(3)
        n = f"{prefix}{n}"
    return n


def image_for(set_code, num, fallback_by_name):
    """Exact print image from the set code + number, else any English print of
    the same card already in cards.json, else None."""
    if set_code and num:
        sid = CODE_TO_ID.get(str(set_code).strip())
        if sid:
            n = card_number(num, sid)
            if sid in SCRYDEX_IDS:
                return f"https://images.scrydex.com/pokemon/{sid}-{n}/large"
            return f"https://images.pokemontcg.io/{sid}/{n}_hires.png"
    return fallback_by_name


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XLSX
    try:
        import openpyxl
    except ImportError:
        sys.exit("ERROR: openpyxl not installed. Run: .venv/bin/pip install openpyxl")
    if not Path(xlsx).exists():
        sys.exit(f"ERROR: spreadsheet not found: {xlsx}")

    cards = json.loads(CARDS.read_text(encoding="utf-8"))
    img_by_name = {}
    for c in cards:
        k = name_key(c["name"])
        if k not in img_by_name and c.get("image"):
            img_by_name[k] = c["image"]

    wb = openpyxl.load_workbook(xlsx, data_only=True)
    rows = list(wb["Collection"].iter_rows(values_only=True))

    groups = OrderedDict()
    for r in rows[1:]:
        name = r[0]
        if not name:
            continue
        name = re.sub(r"\s+", " ", str(name)).strip()
        card_type, set_code, num, version, qty = r[1], r[2], r[3], r[4], r[5]
        qty = int(qty or 0)
        if qty <= 0:
            continue
        k = name_key(name)
        g = groups.setdefault(k, {
            "name": re.sub(r"\s*\([^)]*\)\s*$", "", name).strip(),
            "type": card_type or "",
            "key": k, "total": 0, "variants": [],
        })
        g["total"] += qty
        v_key = (version or "Standard", str(set_code or "").strip(), str(num or "").strip())
        existing = next((v for v in g["variants"]
                         if (v["version"], v["set"], v["num"]) == v_key), None)
        if existing:            # same print listed on more than one sheet row
            existing["qty"] += qty
            continue
        g["variants"].append({
            "version": v_key[0], "set": v_key[1], "num": v_key[2],
            "qty": qty, "source": "Spare",
            "image": image_for(set_code, num, img_by_name.get(k)),
        })

    out = sorted(groups.values(), key=lambda g: g["name"].lower())
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    copies = sum(g["total"] for g in out)
    no_img = sum(1 for g in out for v in g["variants"] if not v["image"])
    in_deck = sum(1 for g in out if g["key"] in {name_key(c["name"]) for c in cards})
    print(f"Wrote {len(out)} cards ({copies} copies) to {OUT}")
    print(f"  variants without an image: {no_img}")
    print(f"  cards used in at least one deck: {in_deck} (rest show as Spare)")


if __name__ == "__main__":
    main()
