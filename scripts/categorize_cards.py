"""Add a "category" field (Pokemon / Trainer / Energy) to every row in
data/cards.json.

There's no type column anywhere in the source spreadsheet (checked the
MasterTable, Template, and per-year sheets — all four are just
Year/Deck/Count/Name/Set), so categories are assigned from an explicit,
hand-checked lookup of the collection's 578 unique card names. Names not
found in ENERGY_NAMES or TRAINER_NAMES default to Pokemon, which is safe
because Trainers and Energy are closed, well-known vocabularies while
Pokemon species/forms are not.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS_JSON = ROOT / "data" / "cards.json"

ENERGY_NAMES = {
    "Aurora Energy", "Beast Energy Prism Star", "Blend Energy WLFM", "Call Energy",
    "Capture Energy", "Cyclone Energy", "Darkness Energy", "Double Colorless Energy",
    "Double Dragon Energy", "Double Turbo Energy", "Fairy Energy", "Fighting Energy",
    "Fire Energy", "Fusion Strike Energy", "Gift Energy", "Grass Energy", "Jet Energy",
    "Lightning Energy", "Luminous Energy", "Metal Energy", "Neo Upper Energy",
    "Plasma Energy", "Prism Energy", "Psychic Energy", "Rainbow Energy",
    "Rapid Strike Energy", "Reversal Energy", "Spiral Energy", "Splash Energy",
    "Strong Energy", "Therapeutic Energy", "Unit Energy GRW", "Unit Energy LPM",
    "V Guard Energy", "Warp Energy", "Water Energy", "Wonder Energy",
}

TRAINER_NAMES = {
    "AZ", "Aaron's Collection", "Ace Trainer", "Acerola", "Acro Bike", "Adventure Bag",
    "Air Balloon", "Ancient Booster Energy Capsule", "Aqua Patch", "Archie's Ace in the Hole",
    "Area Zero Underdepths", "Artazon", "Arven", "Audino Spirit Link", "Battle Compressor",
    "Battle VIP Pass", "Beast Bringer", "Beast Ring", "Bebe's Search", "Bianca", "Bicycle",
    "Big Charm", "Bill's Analysis", "Boss's Orders", "Box of Disaster", "Bravery Charm",
    "Brawly", "Brigette", "Brock's Scouting", "Broken Time-Space", "Brooklet Hill",
    "Buddy-Buddy Poffin", "Bursting Balloon", "Canceling Cologne", "Capacious Bucket",
    "Capturing Aroma", "Cherish Ball", "Cheryl", "Choice Band", "Choice Belt",
    "Collapsed Stadium", "Colress", "Colress Machine", "Colress's Experiment",
    "Colress's Tenacity", "Computer Search", "Counter Catcher", "Cram-o-matic",
    "Crispin", "Crushing Hammer", "Crystal Cave", "Custom Catcher", "Cynthia",
    "Cynthia & Caitlin", "Cynthia's Ambition", "Cynthia's Feelings", "Cyrus's Conspiracy",
    "Dark Claw", "Dark Patch", "Defiance Band", "Delinquent", "Dimension Valley",
    "Dive Ball", "Dowsing Machine", "Dual Ball", "Earthen Vessel", "Echoing Horn",
    "Electric Generator", "Electromagnetic Radar", "Electropower", "Elesa's Sparkle",
    "Energy Loto", "Energy Recycler", "Energy Retrieval", "Energy Search",
    "Energy Spinner", "Energy Switch", "Enhanced Hammer", "Escape Board", "Escape Rope",
    "Eviolite", "Evolution Incense", "Evosoda", "Expert Belt", "Explorer's Guidance",
    "Fairy Garden", "Felicity's Drawing", "Field Blower", "Fiery Flint",
    "Fighting Fury Belt", "Fighting Stadium", "Fire Crystal", "Fisherman", "Float Stone",
    "Fog Crystal", "Forest Seal Stone", "Forest of Giant Plants", "Friend Ball",
    "Future Booster Energy Capsule", "G Booster", "Giant Hearth", "Giovanni's Charisma",
    "Great Catcher", "Great Potion", "Green's Exploration", "Guzma", "Guzma & Hala",
    "Heat Factory Prism Star", "Heavy Ball", "Hex Maniac", "Hilda", "Hisuian Heavy Ball",
    "Hypnotoxic Laser", "Iono", "Irida", "Jamming Tower", "Judge", "Junk Arm", "Karen",
    "Kiawe", "Klara", "Korrina", "Korrina's Focus", "Leon", "Level Ball", "Levincia",
    "Lillie", "Looker's Investigation", "Lost City", "Lost Vacuum", "Lucian's Assignment",
    "Lucky Egg", "Luxury Ball", "Lysandre", "Lysandre Labs", "Mallow", "Marnie",
    "Max Elixir", "Max Potion", "Mega Turbo", "Melony", "Metal Saucer", "Mirage Gate",
    "Mixed Herbs", "Moonlight Stadium", "Multi Switch", "Muscle Band",
    "Mysterious Treasure", "N", "Nest Ball", "Night Maintenance", "Night Stretcher",
    "Ordinary Rod", "Pal Pad", "Parallel City", "Path to the Peak", "Penny",
    "PokéStop", "Pokégear 3.0", "Pokémon Catcher", "Pokémon Center Lady",
    "Pokémon Collector", "Pokémon Communication", "Pokémon Fan Club", "Pokémon Ranger",
    "Pokémon Rescue",
    "Potion", "Power Plant", "Power Tablet", "PlusPower", "Prime Catcher", "Professor Burnet",
    "Professor Juniper", "Professor Kukui", "Professor Oak's New Theory",
    "Professor Sada's Vitality", "Professor Sycamore", "Professor Turo's Scenario",
    "Professor's Letter", "Professor's Research", "Puzzle of Time", "Quick Ball",
    "Raihan", "Random Receiver", "Rare Candy", "Rayquaza Spirit Link", "Rescue Board",
    "Rescue Carrier", "Rescue Stretcher", "Reset Stamp", "Reverse Valley", "Revitalizer",
    "Revive", "Rose Tower", "Roseanne's Research", "Rotom Phone", "Rough Seas",
    "Roxanne", "Scoop Up Cyclone", "Scoop Up Net", "Scramble Switch", "Secret Box",
    "Shadow Triad", "Shauna", "Shrine of Punishment", "Silent Lab", "Sky Field",
    "Skyarrow Bridge", "Skyla", "Special Charge", "Spell Tag", "Stadium Nav",
    "Startling Megaphone", "Super Rod", "Super Scoop Up", "Superior Energy Retrieval",
    "Switch", "Switch Cart", "Tag Call", "Tag Switch", "Target Whistle",
    "Team Galactic's Invention G-101 Energy Gain",
    "Team Galactic's Invention G-103 Power Spray",
    "Team Galactic's Invention G-105 Poke Turn",
    "Team Galactic's Invention G-109 SP Radar", "Team Plasma Ball",
    "Team Rocket's Petrel", "Teammates", "Technical Machine: Devolution",
    "Technical Machine: Evolution", "Technical Machine: Turbo Energize", "Techno Radar",
    "Temple of Sinnoh", "Thunder Mountain Prism Star", "Tool Jammer", "Tool Scrapper",
    "Tower of Waters", "Town Map", "Town Store", "Trainers' Mail", "Training Court",
    "Tropical Beach", "Ultra Ball", "Ultra Space", "VS Seeker", "Virbank City Gym",
    "Viridian Forest", "Vitality Band", "Volkner", "Warp Point", "Welder", "Xerosic",
}


def main():
    cards = json.loads(CARDS_JSON.read_text(encoding="utf-8"))

    def categorize(name: str) -> str:
        if name in ENERGY_NAMES:
            return "Energy"
        if name in TRAINER_NAMES:
            return "Trainer"
        return "Pokemon"

    for c in cards:
        c["category"] = categorize(c["name"])

    CARDS_JSON.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = {"Pokemon": 0, "Trainer": 0, "Energy": 0}
    for c in cards:
        counts[c["category"]] += 1
    print(f"Categorized {len(cards)} rows: {counts}")


if __name__ == "__main__":
    main()
