# Vig's Pokémon TCG Old Format Collection

A static site for browsing a personal Pokémon TCG collection: 67 competitive decks
spanning 2010–2025, each with its full card list and (for most decks) a "how to
pilot" guide.

Live site: served from `index.html` via GitHub Pages.

## How it's built

- `index.html` — the whole app (HTML/CSS/JS, no build step, no framework). It
  fetches its data at load time from the `data/` folder, supports a light/dark
  theme toggle (remembered via `localStorage`), and opens a card's image in a
  modal when you click it.
- `data/cards.json` — every card line for every deck (year, deck name, count,
  card name, set number, `category` of Pokemon/Trainer/Energy, and an `image`
  URL where one was found).
- `data/guides.json` — piloting-guide HTML for each deck, keyed by a slug of
  the deck name (see `slug()` in `index.html`).
- `data/turn1_rules.json` — the "player going first" ruleset for each `year`
  label (coin flip, and what's allowed on turn 1), shown in an expandable
  box when a single year is filtered. Hand-maintained; see `TURN1_RULES.md`
  for the research and sources behind it.
- `piloting_guides_collection/` — the source markdown for every guide, one
  file per deck, organized by year. This is the thing to edit if you want to
  change a guide's content.
- `Old_Format_Collection_20102025.xlsx` — the source spreadsheet the card data
  was originally compiled from.
- `card_collection_with_urls.csv` — Name/Set/Set Code/Image URL for every
  known card print, used to attach `image` to each row in `cards.json`.

## Updating content

To change a guide's writeup, edit its `.md` file under
`piloting_guides_collection/<year>/`, then regenerate `data/guides.json`:

```bash
python3 -m venv .venv        # first time only
.venv/bin/pip install -r requirements.txt   # first time only
.venv/bin/python scripts/build_guides.py
```

To change the card data, edit `data/cards.json` directly (or regenerate it
from a fresh spreadsheet export — see `scripts/extract_cards.py` for the
original one-off extraction logic). If you add new cards, rerun
`scripts/categorize_cards.py` (Pokemon/Trainer/Energy — see the
hand-checked `ENERGY_NAMES`/`TRAINER_NAMES` lists at the top of that file;
anything not in either list defaults to Pokemon) and
`scripts/merge_image_urls.py` (pulls `image` URLs from
`card_collection_with_urls.csv` by matching name + set) to fill in the new
rows' `category` and `image` fields.

Then just refresh the page (or push to GitHub — Pages redeploys automatically
on every push to `main`).
