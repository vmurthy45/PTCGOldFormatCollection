"""Merge card_collection_with_urls.csv (Name, Set, Set Code, Image URL) into
data/cards.json by (name, set), adding an "image" field to each row.

The CSV itself flags cards it couldn't resolve with placeholder values
("Not Found" / "Error" instead of a URL) rather than leaving the field
blank or omitting the row — those must be filtered out, not treated as a
match, or the placeholder string ends up stored as if it were a real image
URL (which happened in an earlier version of this script).

URL_OVERRIDES fills in cards the CSV never resolved at all, hand-verified
(HTTP 200, matching pokemontcg.io set code) after the user supplied them.

NAME_FIXES normalizes spelling variants that appear inconsistently in both
cards.json and the CSV (mojibake, missing accents, doubled spaces) to one
canonical spelling, applied to both sources before the (name, set) join so
a row isn't missed just because the CSV spelled that print's name
differently from cards.json.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS_JSON = ROOT / "data" / "cards.json"
CSV_PATH = ROOT / "card_collection_with_urls.csv"

NAME_FIXES = {
    "Pok√©mon Catcher": "Pokémon Catcher",  # UTF-8/Latin-1 mojibake
    "Pokemon Catcher": "Pokémon Catcher",
    "Pokemon Collector": "Pokémon Collector",
    "Pokemon  Collector": "Pokémon Collector",  # doubled space in the source spreadsheet
    "Pokemon Communication": "Pokémon Communication",
    "Pokemon Rescue": "Pokémon Rescue",
}

# (name, set) -> image URL, for prints the CSV flagged as "Not Found"/"Error"
# with no working row at all. Verified HTTP 200 before adding.
URL_OVERRIDES = {
    ("Air Balloon", "156/202"): "https://images.pokemontcg.io/swsh1/156_hires.png",
    ("Crushing Hammer", "115/149"): "https://images.pokemontcg.io/sm1/115_hires.png",
    ("Lt. Surge's Strategy", "178/214"): "https://images.pokemontcg.io/sm10/178_hires.png",
    ("Bellelba & Brycen-Man", "186/236"): "https://images.pokemontcg.io/sm12/186_hires.png",
    ("Faba", "173/214"): "https://images.pokemontcg.io/sm8/173_hires.png",
    ("Tate & Liza", "148/168"): "https://images.pokemontcg.io/sm7/148_hires.png",
    ("Lillie's Poké Doll", "197/236"): "https://images.pokemontcg.io/sm12/197_hires.png",
    ("Great Ball", "119/149"): "https://images.pokemontcg.io/sm1/119_hires.png",
    ("Recycle Energy", "212/236"): "https://images.pokemontcg.io/sm11/212_hires.png",
    ("Team Galactic's Invention G-105 Poke Turn", "118/127"): "https://images.pokemontcg.io/pl1/118_hires.png",
    ("Unown Q", "49/100"): "https://images.pokemontcg.io/dp5/49_hires.png",
    ("Unown R", "77/146"): "https://images.pokemontcg.io/dp6/77_hires.png",
    ("Unown G", "57/106"): "https://images.pokemontcg.io/dp4/57_hires.png",
    ("Switch", "104/114"): "https://images.pokemontcg.io/bw9/104_hires.png",
    ("Blend Energy WLFM", "118/124"): "https://images.pokemontcg.io/bw6/118_hires.png",
    ("Unit Energy LPM", "138/156"): "https://images.pokemontcg.io/sm5/138_hires.png",
    ("Pikachu & Zekrom-GX", "33/181"): "https://images.pokemontcg.io/sm9/33_hires.png",
    ("Reshiram & Charizard-GX", "20/214"): "https://images.pokemontcg.io/sm10/20_hires.png",
    ("Raichu & Alolan Raichu-GX", "54/236"): "https://images.pokemontcg.io/sm11/54_hires.png",
    ("Mewtwo & Mew-GX", "71/236"): "https://images.pokemontcg.io/sm11/71_hires.png",
    ("Espeon & Deoxys-GX", "72/236"): "https://images.pokemontcg.io/sm11/72_hires.png",
    ("Arceus & Dialga & Palkia-GX", "156/236"): "https://images.pokemontcg.io/sm12/156_hires.png",
    ("Guzma & Hala", "193/236"): "https://images.pokemontcg.io/sm12/193_hires.png",
    ("Cynthia & Caitlin", "189/236"): "https://images.pokemontcg.io/sm12/189_hires.png",
    ("Unit Energy GRW", "137/156"): "https://images.pokemontcg.io/sm5/137_hires.png",
    ("Rapid Strike Energy", "140/163"): "https://images.pokemontcg.io/swsh5/140_hires.png",
    # Whimsicott GX (2019) — new cards for this deck, all HTTP-verified 200.
    ("Cottonee", "139/214"): "https://images.pokemontcg.io/sm10/139_hires.png",
    ("Whimsicott GX", "140/214"): "https://images.pokemontcg.io/sm10/140_hires.png",
    ("Blitzle", "81/214"): "https://images.pokemontcg.io/sm8/81_hires.png",
    ("Zebstrika", "82/214"): "https://images.pokemontcg.io/sm8/82_hires.png",
    ("Porygon", "155/214"): "https://images.pokemontcg.io/sm10/155_hires.png",
    ("Porygon-Z", "157/214"): "https://images.pokemontcg.io/sm10/157_hires.png",
    ("Whimsicott", "144/236"): "https://images.pokemontcg.io/sm11/144_hires.png",
    ("Fairy Charm L", "172/214"): "https://images.pokemontcg.io/sm10/172_hires.png",
    ("Wondrous Labyrinth", "158/181"): "https://images.pokemontcg.io/sm9/158_hires.png",
    ("Professor Elm's Lecture", "188/214"): "https://images.pokemontcg.io/sm8/188_hires.png",
    ("Unit Energy FDF", "118/131"): "https://images.pokemontcg.io/sm6/118_hires.png",
    ("Triple Acceleration Energy", "190/214"): "https://images.pokemontcg.io/sm10/190_hires.png",
    # Rainbow Energy's only in-collection prints are XY-era (not 2019-legal);
    # this deck uses the Celestial Storm 151/168 print.
    ("Rainbow Energy", "151/168"): "https://images.pokemontcg.io/sm7/151_hires.png",
    # Zubat 53/135 (Boundaries Crossed) — the correct print for the two 2015
    # decks; recorded here (not just in cards.json) so it survives a re-merge.
    ("Zubat", "53/135"): "https://images.pokemontcg.io/bw8/53_hires.png",
    # ADP Zacian (2020) Limitless Invitational list — new prints for this deck,
    # all HTTP-verified 200.
    ("Oranguru", "148/202"): "https://images.pokemontcg.io/swsh1/148_hires.png",
    ("Eldegoss V", "19/192"): "https://images.pokemontcg.io/swsh2/19_hires.png",
    ("Mallow & Lana", "198/236"): "https://images.pokemontcg.io/sm12/198_hires.png",
    ("Order Pad", "131/156"): "https://images.pokemontcg.io/sm5/131_hires.png",
    ("Energy Switch", "162/202"): "https://images.pokemontcg.io/swsh1/162_hires.png",
    ("Metal Frying Pan", "112/131"): "https://images.pokemontcg.io/sm6/112_hires.png",
    ("Chaotic Swell", "187/236"): "https://images.pokemontcg.io/sm12/187_hires.png",
    # 2021 (Players Cup III/IV) decks — Limitless-archived lists; all
    # HTTP-verified 200. Professor's Research is shown as its 2021-era
    # SSH print rather than the newest reprint Limitless displays.
    ('Air Balloon', '156/202'): 'https://images.pokemontcg.io/swsh1/156_hires.png',
    ('Bird Keeper', '159/189'): 'https://images.pokemontcg.io/swsh3/159_hires.png',
    ("Boss's Orders", '154/192'): 'https://images.pokemontcg.io/swsh2/154_hires.png',
    ('Capacious Bucket', '156/192'): 'https://images.pokemontcg.io/swsh2/156_hires.png',
    ('Cape of Toughness', '160/189'): 'https://images.pokemontcg.io/swsh3/160_hires.png',
    ('Chaotic Swell', '187/236'): 'https://images.pokemontcg.io/sm12/187_hires.png',
    ('Crobat V', '104/189'): 'https://images.pokemontcg.io/swsh3/104_hires.png',
    ('Crushing Hammer', '159/202'): 'https://images.pokemontcg.io/swsh1/159_hires.png',
    ('Dedenne-GX', '57/214'): 'https://images.pokemontcg.io/sm10/57_hires.png',
    ('Drizzile', '56/202'): 'https://images.pokemontcg.io/swsh1/56_hires.png',
    ('Escape Rope', '125/163'): 'https://images.pokemontcg.io/swsh5/125_hires.png',
    ('Eternatus V', '116/189'): 'https://images.pokemontcg.io/swsh3/116_hires.png',
    ('Eternatus VMAX', '117/189'): 'https://images.pokemontcg.io/swsh3/117_hires.png',
    ('Evolution Incense', '163/202'): 'https://images.pokemontcg.io/swsh1/163_hires.png',
    ('Fog Crystal', '140/198'): 'https://images.pokemontcg.io/swsh6/140_hires.png',
    ('Galarian Zigzagoon', '117/202'): 'https://images.pokemontcg.io/swsh1/117_hires.png',
    ('Gengar & Mimikyu-GX', '53/181'): 'https://images.pokemontcg.io/sm9/53_hires.png',
    ('Great Ball', '164/202'): 'https://images.pokemontcg.io/swsh1/164_hires.png',
    ('Hiding Darkness Energy', '175/189'): 'https://images.pokemontcg.io/swsh3/175_hires.png',
    ('Hoopa', '111/189'): 'https://images.pokemontcg.io/swsh3/111_hires.png',
    ('Hoopa', '140/236'): 'https://images.pokemontcg.io/sm11/140_hires.png',
    ('Ice Rider Calyrex V', '45/198'): 'https://images.pokemontcg.io/swsh6/45_hires.png',
    ('Ice Rider Calyrex VMAX', '46/198'): 'https://images.pokemontcg.io/swsh6/46_hires.png',
    ('Inteleon', '43/198'): 'https://images.pokemontcg.io/swsh6/43_hires.png',
    ('Inteleon', '58/202'): 'https://images.pokemontcg.io/swsh1/58_hires.png',
    ('Jirachi', '99/181'): 'https://images.pokemontcg.io/sm9/99_hires.png',
    ('Jirachi-GX', '79/236'): 'https://images.pokemontcg.io/sm11/79_hires.png',
    ('Jynx', '76/236'): 'https://images.pokemontcg.io/sm11/76_hires.png',
    ('Karate Belt', '201/236'): 'https://images.pokemontcg.io/sm11/201_hires.png',
    ('Level Ball', '129/163'): 'https://images.pokemontcg.io/swsh5/129_hires.png',
    ('Marnie', '169/202'): 'https://images.pokemontcg.io/swsh1/169_hires.png',
    ('Marshadow', '103/236'): 'https://images.pokemontcg.io/sm12/103_hires.png',
    ('Marshadow', '81/214'): 'https://images.pokemontcg.io/sm10/81_hires.png',
    ('Melony', '146/198'): 'https://images.pokemontcg.io/swsh6/146_hires.png',
    ('Mew', '76/214'): 'https://images.pokemontcg.io/sm10/76_hires.png',
    ('Mewtwo', '75/214'): 'https://images.pokemontcg.io/sm10/75_hires.png',
    ('Ordinary Rod', '171/202'): 'https://images.pokemontcg.io/swsh1/171_hires.png',
    ('Oricorio-GX', '95/236'): 'https://images.pokemontcg.io/sm12/95_hires.png',
    ('Pal Pad', '172/202'): 'https://images.pokemontcg.io/swsh1/172_hires.png',
    ('Passimian', '88/198'): 'https://images.pokemontcg.io/swsh6/88_hires.png',
    ('Path to the Peak', '148/198'): 'https://images.pokemontcg.io/swsh6/148_hires.png',
    ('Phoebe', '130/163'): 'https://images.pokemontcg.io/swsh5/130_hires.png',
    ('Pokémon Communication', '152/181'): 'https://images.pokemontcg.io/sm9/152_hires.png',
    ("Professor's Research", '178/202'): 'https://images.pokemontcg.io/swsh1/178_hires.png',
    ('Quick Ball', '179/202'): 'https://images.pokemontcg.io/swsh1/179_hires.png',
    ('Rapid Strike Energy', '140/163'): 'https://images.pokemontcg.io/swsh5/140_hires.png',
    ('Rapid Strike Urshifu V', '87/163'): 'https://images.pokemontcg.io/swsh5/87_hires.png',
    ('Rapid Strike Urshifu VMAX', '88/163'): 'https://images.pokemontcg.io/swsh5/88_hires.png',
    ('Reset Stamp', '206/236'): 'https://images.pokemontcg.io/sm11/206_hires.png',
    ('Scoop Up Net', '165/192'): 'https://images.pokemontcg.io/swsh2/165_hires.png',
    ('Shadow Rider Calyrex V', '74/198'): 'https://images.pokemontcg.io/swsh6/74_hires.png',
    ('Shadow Rider Calyrex VMAX', '75/198'): 'https://images.pokemontcg.io/swsh6/75_hires.png',
    ('Sobble', '41/198'): 'https://images.pokemontcg.io/swsh6/41_hires.png',
    ('Spikemuth', '170/189'): 'https://images.pokemontcg.io/swsh3/170_hires.png',
    ('Spiritomb', '112/214'): 'https://images.pokemontcg.io/sm10/112_hires.png',
    ('Switch', '183/202'): 'https://images.pokemontcg.io/swsh1/183_hires.png',
    ('Tool Scrapper', '168/192'): 'https://images.pokemontcg.io/swsh2/168_hires.png',
    ('Tower of Waters', '138/163'): 'https://images.pokemontcg.io/swsh5/138_hires.png',
    ('Weakness Guard Energy', '213/236'): 'https://images.pokemontcg.io/sm11/213_hires.png',
    ('Yveltal', '95/181'): 'https://images.pokemontcg.io/sm9/95_hires.png',
    # Basic Energy is recorded in cards.json with no specific print (empty
    # set), since decklists rarely note which printing was used. These pin
    # every basic Energy card to its XY base-set art (xy1) so there's a
    # consistent, working image to show.
    ("Grass Energy", ""): "https://images.pokemontcg.io/xy1/132_hires.png",
    ("Fire Energy", ""): "https://images.pokemontcg.io/xy1/133_hires.png",
    ("Water Energy", ""): "https://images.pokemontcg.io/xy1/134_hires.png",
    ("Lightning Energy", ""): "https://images.pokemontcg.io/xy1/135_hires.png",
    ("Psychic Energy", ""): "https://images.pokemontcg.io/xy1/136_hires.png",
    ("Fighting Energy", ""): "https://images.pokemontcg.io/xy1/137_hires.png",
    ("Darkness Energy", ""): "https://images.pokemontcg.io/xy1/138_hires.png",
    ("Metal Energy", ""): "https://images.pokemontcg.io/xy1/139_hires.png",
    ("Fairy Energy", ""): "https://images.pokemontcg.io/xy1/140_hires.png",
}


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    url_by_key = {}
    for r in rows:
        if not r["Image URL"].startswith("http"):
            continue  # "Not Found" / "Error" placeholders, not real URLs
        name = NAME_FIXES.get(r["Name"], r["Name"])
        url_by_key[(name, r["Set"])] = r["Image URL"]

    cards = json.loads(CARDS_JSON.read_text(encoding="utf-8"))

    matched = 0
    overridden = 0
    for c in cards:
        name = NAME_FIXES.get(c["name"], c["name"])
        c["name"] = name
        key = (name, c["set"])
        url = url_by_key.get(key) or URL_OVERRIDES.get(key)
        if url:
            if key in URL_OVERRIDES and key not in url_by_key:
                overridden += 1
            c["image"] = url
            matched += 1
        elif "image" in c:
            del c["image"]  # clear any stale/bad value from a previous run

    CARDS_JSON.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Matched images for {matched}/{len(cards)} rows ({overridden} via URL_OVERRIDES); "
          f"{len(cards) - matched} rows still without an image, mostly basic Energy with no set number")


if __name__ == "__main__":
    main()
