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
    # Charizard Pidgeot (2025)
    ("Charmander", "7/91"): "https://images.pokemontcg.io/sv4pt5/7_hires.png",
    ("Charmeleon", "5/165"): "https://images.pokemontcg.io/sv3pt5/5_hires.png",
    ("Charizard ex", "125/197"): "https://images.pokemontcg.io/sv3/125_hires.png",
    ("Pidgey", "162/197"): "https://images.pokemontcg.io/sv3/162_hires.png",
    ("Pidgeotto", "17/165"): "https://images.pokemontcg.io/sv3pt5/17_hires.png",
    ("Pidgeot ex", "164/197"): "https://images.pokemontcg.io/sv3/164_hires.png",
    ("Cleffa", "80/197"): "https://images.pokemontcg.io/sv3/80_hires.png",
    ("Chi-Yu", "29/182"): "https://images.pokemontcg.io/sv4/29_hires.png",
    ("Fezandipiti ex", "38/64"): "https://images.pokemontcg.io/sv6pt5/38_hires.png",
    ("Arven", "186/197"): "https://images.pokemontcg.io/sv3/186_hires.png",
    ("Iono", "185/193"): "https://images.pokemontcg.io/sv2/185_hires.png",
    ("Jacq", "175/198"): "https://images.pokemontcg.io/sv1/175_hires.png",
    ("Briar", "132/142"): "https://images.pokemontcg.io/sv7/132_hires.png",
    ("Rare Candy", "191/198"): "https://images.pokemontcg.io/sv1/191_hires.png",
    ("Counter Catcher", "160/182"): "https://images.pokemontcg.io/sv4/160_hires.png",
    ("Super Rod", "188/193"): "https://images.pokemontcg.io/sv2/188_hires.png",
    ("Nest Ball", "181/198"): "https://images.pokemontcg.io/sv1/181_hires.png",
    ("Technical Machine: Evolution", "178/182"): "https://images.pokemontcg.io/sv4/178_hires.png",
    ("Air Balloon", "79/86"): "https://images.pokemontcg.io/zsv10pt5/79_hires.png",
    ("Maximum Belt", "154/162"): "https://images.pokemontcg.io/sv5/154_hires.png",
    ("Artazon", "171/193"): "https://images.pokemontcg.io/sv2/171_hires.png",
    ("Mist Energy", "161/162"): "https://images.pokemontcg.io/sv5/161_hires.png",
    # Slowking (2026)
    ("Slowpoke", "57/142"): "https://images.pokemontcg.io/sv7/57_hires.png",
    ("Slowking", "58/142"): "https://images.pokemontcg.io/sv7/58_hires.png",
    ("Mega Kangaskhan ex", "104/132"): "https://images.pokemontcg.io/me1/104_hires.png",
    ("Latias ex", "76/191"): "https://images.pokemontcg.io/sv8/76_hires.png",
    ("Kyurem", "47/64"): "https://images.pokemontcg.io/sv6pt5/47_hires.png",
    ("Metagross", "61/86"): "https://images.scrydex.com/pokemon/me4-61/large",
    ("Zeraora", "78/182"): "https://images.pokemontcg.io/sv10/78_hires.png",
    ("Ciphermaniac's Codebreaking", "145/162"): "https://images.pokemontcg.io/sv5/145_hires.png",
    ("Wondrous Patch", "94/94"): "https://images.pokemontcg.io/me2/94_hires.png",
    ("Switch", "130/132"): "https://images.pokemontcg.io/me1/130_hires.png",
    ("Brave Bangle", "80/86"): "https://images.pokemontcg.io/rsv10pt5/80_hires.png",
    ("Academy at Night", "54/64"): "https://images.pokemontcg.io/sv6pt5/54_hires.png",
    ("Boomerang Energy", "166/167"): "https://images.pokemontcg.io/sv6/166_hires.png",
    # N's Zoroark (2026)
    ("N's Zorua", "97/159"): "https://images.pokemontcg.io/sv9/97_hires.png",
    ("N's Zoroark ex", "98/159"): "https://images.pokemontcg.io/sv9/98_hires.png",
    ("N's Zekrom", "155/217"): "https://images.scrydex.com/pokemon/me2pt5-155/large",
    ("N's Darumaka", "26/159"): "https://images.pokemontcg.io/sv9/26_hires.png",
    ("N's Darmanitan", "27/159"): "https://images.pokemontcg.io/sv9/27_hires.png",
    ("Tatsugiri", "131/167"): "https://images.pokemontcg.io/sv6/131_hires.png",
    ("Yveltal", "88/132"): "https://images.pokemontcg.io/me1/88_hires.png",
    ("Pecharunt ex", "39/64"): "https://images.pokemontcg.io/sv6pt5/39_hires.png",
    ("Cyrano", "170/191"): "https://images.pokemontcg.io/sv8/170_hires.png",
    ("Black Belt's Training", "143/159"): "https://images.pokemontcg.io/sv9/143_hires.png",
    ("Ruffian", "157/159"): "https://images.pokemontcg.io/sv9/157_hires.png",
    ("Transformation Tome", "83/86"): "https://images.scrydex.com/pokemon/me4-83/large",
    ("N's PP Up", "153/159"): "https://images.pokemontcg.io/sv9/153_hires.png",
    ("Secret Box", "163/167"): "https://images.pokemontcg.io/sv6/163_hires.png",
    ("Binding Mochi", "95/131"): "https://images.pokemontcg.io/sv8pt5/95_hires.png",
    ("N's Castle", "152/159"): "https://images.pokemontcg.io/sv9/152_hires.png",
    # Hide 'n' Sneak (2026) — PBL = me5 (Pitch Black), scrydex-hosted
    ("Dhelmise", "39/84"): "https://images.scrydex.com/pokemon/me5-39/large",
    ("Shuppet", "33/84"): "https://images.scrydex.com/pokemon/me5-33/large",
    ("Banette", "34/84"): "https://images.scrydex.com/pokemon/me5-34/large",
    ("Poltchageist", "5/84"): "https://images.scrydex.com/pokemon/me5-5/large",
    ("Sinistcha", "6/84"): "https://images.scrydex.com/pokemon/me5-6/large",
    ("Gwynn", "78/84"): "https://images.scrydex.com/pokemon/me5-78/large",
    ("Lillie's Clefairy ex", "56/159"): "https://images.pokemontcg.io/sv9/56_hires.png",
    ("Bloodmoon Ursaluna ex", "141/167"): "https://images.pokemontcg.io/sv6/141_hires.png",
    ("Pokégear 3.0", "186/198"): "https://images.pokemontcg.io/sv1/186_hires.png",
    ("Legacy Energy", "167/167"): "https://images.pokemontcg.io/sv6/167_hires.png",
    # Alakazam (2026)
    ("Abra", "54/132"): "https://images.pokemontcg.io/me1/54_hires.png",
    ("Kadabra", "55/132"): "https://images.pokemontcg.io/me1/55_hires.png",
    ("Alakazam", "56/132"): "https://images.pokemontcg.io/me1/56_hires.png",
    ("Rare Candy", "125/132"): "https://images.pokemontcg.io/me1/125_hires.png",
    ("Dedenne", "87/191"): "https://images.pokemontcg.io/sv8/87_hires.png",
    ("Elgyem", "40/86"): "https://images.pokemontcg.io/zsv10pt5/40_hires.png",
    ("Genesect", "40/64"): "https://images.pokemontcg.io/sv6pt5/40_hires.png",
    ("Shaymin", "10/182"): "https://images.pokemontcg.io/sv10/10_hires.png",
    ("Hilda", "84/86"): "https://images.pokemontcg.io/rsv10pt5/84_hires.png",
    ("Lana's Aid", "155/167"): "https://images.pokemontcg.io/sv6/155_hires.png",
    ("Enhanced Hammer", "148/167"): "https://images.pokemontcg.io/sv6/148_hires.png",
    ("Lucky Helmet", "158/167"): "https://images.pokemontcg.io/sv6/158_hires.png",
    ("Handheld Fan", "150/167"): "https://images.pokemontcg.io/sv6/150_hires.png",
    ("Sacred Ash", "168/182"): "https://images.pokemontcg.io/sv10/168_hires.png",
    ("Enriching Energy", "191/191"): "https://images.pokemontcg.io/sv8/191_hires.png",
    ("Air Balloon", "181/217"): "https://images.scrydex.com/pokemon/me2pt5-181/large",
    ("Nighttime Mine", "197/217"): "https://images.scrydex.com/pokemon/me2pt5-197/large",
    ("Telepathic Psychic Energy", "88/88"): "https://images.scrydex.com/pokemon/me3-88/large",
    # Dragapult (2026)
    ("Dunsparce", "120/159"): "https://images.pokemontcg.io/sv9/120_hires.png",
    ("Dudunsparce", "129/162"): "https://images.pokemontcg.io/sv5/129_hires.png",
    ("Risky Ruins", "127/132"): "https://images.pokemontcg.io/me1/127_hires.png",
    ("Rosa's Encouragement", "84/88"): "https://images.scrydex.com/pokemon/me3-84/large",
    # Dragapult Dusknoir (2026)
    ("Duskull", "35/131"): "https://images.pokemontcg.io/sv8pt5/35_hires.png",
    ("Dusclops", "36/131"): "https://images.pokemontcg.io/sv8pt5/36_hires.png",
    ("Dusknoir", "37/131"): "https://images.pokemontcg.io/sv8pt5/37_hires.png",
    ("Budew", "16/217"): "https://images.scrydex.com/pokemon/me2pt5-16/large",
    ("Fezandipiti ex", "142/217"): "https://images.scrydex.com/pokemon/me2pt5-142/large",
    ("Meowth ex", "62/88"): "https://images.scrydex.com/pokemon/me3-62/large",
    ("Lillie's Determination", "119/132"): "https://images.pokemontcg.io/me1/119_hires.png",
    ("Boss's Orders", "114/132"): "https://images.pokemontcg.io/me1/114_hires.png",
    ("Dawn", "87/94"): "https://images.pokemontcg.io/me2/87_hires.png",
    ("Crushing Hammer", "71/88"): "https://images.scrydex.com/pokemon/me3-71/large",
    ("Unfair Stamp", "165/167"): "https://images.pokemontcg.io/sv6/165_hires.png",
    ("Special Red Card", "82/86"): "https://images.scrydex.com/pokemon/me4-82/large",
    ("Team Rocket's Watchtower", "180/182"): "https://images.pokemontcg.io/sv10/180_hires.png",
    ("Rayquaza-GX", "109/168"): "https://images.pokemontcg.io/sm7/109_hires.png",
    ("Marshadow", "45/73"): "https://images.pokemontcg.io/sm35/45_hires.png",
    ("Escape Rope", "114/147"): "https://images.pokemontcg.io/sm3/114_hires.png",
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
    # 2017 Worlds format prints (Tapu Bulu Vikavolt / Espeon Garbodor /
    # Drampa Garbodor / Decidueye Ninetales) that the CSV didn't resolve.
    ('Eevee', '101/149'): 'https://images.pokemontcg.io/sm1/101_hires.png',
    ('Ultra Ball', '135/149'): 'https://images.pokemontcg.io/sm1/135_hires.png',
    ('Double Colorless Energy', '136/149'): 'https://images.pokemontcg.io/sm1/136_hires.png',
    ('Rainbow Energy', '137/149'): 'https://images.pokemontcg.io/sm1/137_hires.png',
    ('Plumeria', '120/147'): 'https://images.pokemontcg.io/sm3/120_hires.png',
    # Greninja BREAK (2018) prints the CSV didn't resolve.
    ('Froakie', '38/122'): 'https://images.pokemontcg.io/xy9/38_hires.png',
    ('Staryu', '25/122'): 'https://images.pokemontcg.io/xy9/25_hires.png',
    ('Starmie', '31/108'): 'https://images.pokemontcg.io/xy12/31_hires.png',
    ('Evosoda', '116/146'): 'https://images.pokemontcg.io/xy1/116_hires.png',
    # Rocket's Honchkrow (2026). Newest Mega-era sets (me2pt5 "ASC", me3 "POR")
    # aren't on images.pokemontcg.io yet — those three cards use scrydex, the
    # only host that serves them (all HTTP-verified 200).
    ("Team Rocket's Murkrow", '127/182'): 'https://images.pokemontcg.io/sv10/127_hires.png',
    ("Team Rocket's Honchkrow", '127/217'): 'https://images.scrydex.com/pokemon/me2pt5-127/large',
    ("Team Rocket's Porygon", '153/182'): 'https://images.pokemontcg.io/sv10/153_hires.png',
    ("Team Rocket's Porygon2", '154/182'): 'https://images.pokemontcg.io/sv10/154_hires.png',
    ("Team Rocket's Articuno", '51/182'): 'https://images.pokemontcg.io/sv10/51_hires.png',
    ("Team Rocket's Ariana", '171/182'): 'https://images.pokemontcg.io/sv10/171_hires.png',
    ("Team Rocket's Archer", '170/182'): 'https://images.pokemontcg.io/sv10/170_hires.png',
    ("Team Rocket's Giovanni", '174/182'): 'https://images.pokemontcg.io/sv10/174_hires.png',
    ("Team Rocket's Proton", '177/182'): 'https://images.pokemontcg.io/sv10/177_hires.png',
    ("Team Rocket's Petrel", '176/182'): 'https://images.pokemontcg.io/sv10/176_hires.png',
    ('Poké Pad', '81/88'): 'https://images.scrydex.com/pokemon/me3-81/large',
    ("Team Rocket's Transceiver", '178/182'): 'https://images.pokemontcg.io/sv10/178_hires.png',
    ('Roto-Stick', '127/131'): 'https://images.pokemontcg.io/sv8pt5/127_hires.png',
    ('Night Stretcher', '196/217'): 'https://images.scrydex.com/pokemon/me2pt5-196/large',
    ('Ultra Ball', '131/132'): 'https://images.pokemontcg.io/me1/131_hires.png',
    ('Miracle Headset', '183/191'): 'https://images.pokemontcg.io/sv8/183_hires.png',
    ("Team Rocket's Factory", '173/182'): 'https://images.pokemontcg.io/sv10/173_hires.png',
    ("Team Rocket's Energy", '182/182'): 'https://images.pokemontcg.io/sv10/182_hires.png',
    ('Ignition Energy', '86/86'): 'https://images.pokemontcg.io/rsv10pt5/86_hires.png',
    # Malamar (2019) Espurr correction: UNB 79 (was mistakenly FLI 44).
    ('Espurr', '79/214'): 'https://images.pokemontcg.io/sm10/79_hires.png',
    # Cynthia's Garchomp (2026). More Mega-era prints; the me2pt5/me3/me4
    # (ASC/POR/CRI) cards are scrydex-only (verified 200). Poké Pad 81/88 and
    # Night Stretcher 196/217 reuse the overrides added for Rocket's Honchkrow.
    ("Cynthia's Gible", '109/217'): 'https://images.scrydex.com/pokemon/me2pt5-109/large',
    ("Cynthia's Gabite", '110/217'): 'https://images.scrydex.com/pokemon/me2pt5-110/large',
    ("Cynthia's Garchomp ex", '111/217'): 'https://images.scrydex.com/pokemon/me2pt5-111/large',
    ("Cynthia's Roselia", '7/182'): 'https://images.pokemontcg.io/sv10/7_hires.png',
    ("Cynthia's Roserade", '8/182'): 'https://images.pokemontcg.io/sv10/8_hires.png',
    ("Cynthia's Power Weight", '162/182'): 'https://images.pokemontcg.io/sv10/162_hires.png',
    ("Lillie's Determination", '192/217'): 'https://images.scrydex.com/pokemon/me2pt5-192/large',
    ("Boss's Orders", '183/217'): 'https://images.scrydex.com/pokemon/me2pt5-183/large',
    ('Pokégear 3.0', '84/86'): 'https://images.pokemontcg.io/zsv10pt5/84_hires.png',
    ('Fighting Gong', '187/217'): 'https://images.scrydex.com/pokemon/me2pt5-187/large',
    ('Buddy-Buddy Poffin', '184/217'): 'https://images.scrydex.com/pokemon/me2pt5-184/large',
    ('Premium Power Pro', '199/217'): 'https://images.scrydex.com/pokemon/me2pt5-199/large',
    ('Hilda', '84/86'): 'https://images.pokemontcg.io/rsv10pt5/84_hires.png',
    ('Prime Catcher', '119/131'): 'https://images.pokemontcg.io/sv8pt5/119_hires.png',
    ('Switch', '130/132'): 'https://images.pokemontcg.io/me1/130_hires.png',
    ('Prism Tower', '80/86'): 'https://images.scrydex.com/pokemon/me4-80/large',
    ('Rocky Fighting Energy', '87/88'): 'https://images.scrydex.com/pokemon/me3-87/large',
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
    # Rocket's Mewtwo (2026). All pokemontcg.io-hosted (DRI=sv10, MEG=me1, TWM=sv6).
    # The rest of the deck reuses overrides already present above (Team Rocket's
    # supporters, Lillie's line, Ultra Ball, Night Stretcher, Lucky Helmet, etc.).
    ("Team Rocket's Tarountula", "19/182"): "https://images.pokemontcg.io/sv10/19_hires.png",
    ("Team Rocket's Spidops", "20/182"): "https://images.pokemontcg.io/sv10/20_hires.png",
    ("Team Rocket's Mewtwo ex", "81/182"): "https://images.pokemontcg.io/sv10/81_hires.png",
    ("Team Rocket's Mimikyu", "87/182"): "https://images.pokemontcg.io/sv10/87_hires.png",
    ("Bug Catching Set", "143/167"): "https://images.pokemontcg.io/sv6/143_hires.png",
    ("Energy Switch", "115/132"): "https://images.pokemontcg.io/me1/115_hires.png",
    # N's Zoroark (2026) update: N's Reshiram (JTG=sv9).
    ("N's Reshiram", "116/159"): "https://images.pokemontcg.io/sv9/116_hires.png",
    # Alakazam (2026) rebuild. PBL=me5 and ASC=me2pt5 are scrydex-only (verified
    # 200); Battle Cage (PFL=me2) and Buddy-Buddy Poffin (TEF=sv5) are on pokemontcg.io.
    ("Pikipek", "66/84"): "https://images.scrydex.com/pokemon/me5-66/large",
    ("Trumbeak", "67/84"): "https://images.scrydex.com/pokemon/me5-67/large",
    ("Toucannon", "68/84"): "https://images.scrydex.com/pokemon/me5-68/large",
    ("Psyduck", "39/217"): "https://images.scrydex.com/pokemon/me2pt5-39/large",
    ("Battle Cage", "85/94"): "https://images.pokemontcg.io/me2/85_hires.png",
    ("Buddy-Buddy Poffin", "144/162"): "https://images.pokemontcg.io/sv5/144_hires.png",
    # Eternatus VMAX (2021) update: Galarian Moltres V / Liepard V (CRE=swsh6),
    # Big Charm (SSH=swsh1). Energy Switch 162/202 reuses an existing override.
    ("Galarian Moltres V", "97/198"): "https://images.pokemontcg.io/swsh6/97_hires.png",
    ("Liepard V", "104/198"): "https://images.pokemontcg.io/swsh6/104_hires.png",
    ("Big Charm", "158/202"): "https://images.pokemontcg.io/swsh1/158_hires.png",
    # Slowking (2026): Slowpoke swapped to the PAL (sv2) print.
    ("Slowpoke", "85/193"): "https://images.pokemontcg.io/sv2/85_hires.png",
    # Empoleon Swampert (2018) — SM-era (UPR=sm5, CES=sm7, GRI=sm2, BUS=sm3,
    # SUM=sm1, CIN=sm4, SMP=smp promos, all on pokemontcg.io).
    ("Piplup", "32/156"): "https://images.pokemontcg.io/sm5/32_hires.png",
    ("Prinplup", "33/156"): "https://images.pokemontcg.io/sm5/33_hires.png",
    ("Empoleon", "34/156"): "https://images.pokemontcg.io/sm5/34_hires.png",
    ("Mudkip", "33/168"): "https://images.pokemontcg.io/sm7/33_hires.png",
    ("Marshtomp", "34/168"): "https://images.pokemontcg.io/sm7/34_hires.png",
    ("Swampert", "35/168"): "https://images.pokemontcg.io/sm7/35_hires.png",
    ("Tapu Koko", "SM30/248"): "https://images.pokemontcg.io/smp/SM30_hires.png",
    ("Oranguru", "114/156"): "https://images.pokemontcg.io/sm5/114_hires.png",
    ("Alolan Vulpix", "21/145"): "https://images.pokemontcg.io/sm2/21_hires.png",
    ("Cynthia", "119/156"): "https://images.pokemontcg.io/sm5/119_hires.png",
    ("Guzma", "115/147"): "https://images.pokemontcg.io/sm3/115_hires.png",
    ("Lillie", "125/156"): "https://images.pokemontcg.io/sm5/125_hires.png",
    ("Professor Kukui", "128/149"): "https://images.pokemontcg.io/sm1/128_hires.png",
    ("Rare Candy", "142/168"): "https://images.pokemontcg.io/sm7/142_hires.png",
    ("Nest Ball", "123/149"): "https://images.pokemontcg.io/sm1/123_hires.png",
    ("Timer Ball", "134/149"): "https://images.pokemontcg.io/sm1/134_hires.png",
    ("Aqua Patch", "119/145"): "https://images.pokemontcg.io/sm2/119_hires.png",
    ("Rescue Stretcher", "130/145"): "https://images.pokemontcg.io/sm2/130_hires.png",
    ("Choice Band", "121/145"): "https://images.pokemontcg.io/sm2/121_hires.png",
    ("Brooklet Hill", "120/145"): "https://images.pokemontcg.io/sm2/120_hires.png",
    ("Counter Energy", "100/111"): "https://images.pokemontcg.io/sm4/100_hires.png",
    ("Super Boost Energy Prism Star", "136/156"): "https://images.pokemontcg.io/sm5/136_hires.png",
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
