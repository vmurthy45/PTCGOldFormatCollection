# Vig's Pokémon TCG Old Format Collection — agent notes

This file is for a future Claude Code session picking this project back up.
It covers what the site is, how the data pipeline works, exactly what to do
for the next yearly update, the bugs that got found and fixed along the way
(so they don't get reintroduced), and Vig's stated preferences.

Read `README.md` too — it's the human-facing version of the "how it's
built" section below and stays more terse. This file is the deeper,
agent-oriented version: it explains *why*, not just *what*.

## What this is

A static site (no framework, no build step) for browsing Vig's personal
Pokémon TCG collection: one deck per competitive archetype, 2010–2025,
each with its full card list and (for most decks) a "how to pilot" guide.
Hosted free on GitHub Pages.

- Live site: https://vmurthy45.github.io/PTCGOldFormatCollection/
- Repo: https://github.com/vmurthy45/PTCGOldFormatCollection (public —
  required for free GitHub Pages on a personal account)
- Local path: wherever this file lives (was
  `/Users/vighnesh/Downloads/Claude Code Projects/pokemon-old-format-collection`
  as of this writing, but don't hardcode that — check `pwd`)

## Architecture

- `index.html` — the entire app. Vanilla HTML/CSS/JS, no dependencies except
  two Google Fonts (Poppins for headings, Inter for body) loaded via
  `<link>`. Fetches `data/cards.json`, `data/guides.json`, and
  `data/turn1_rules.json` at page load. **Must be served over http(s)** —
  opening it via `file://` breaks the `fetch()` calls (this is a browser
  security restriction, not a bug).
- `data/cards.json` — every card line for every deck. Each row:
  `{year, deck, count, name, set, category, image, prints}`. `prints` is
  `{authentic, wc, proxy}` — how many of the row's `count` copies you own of
  each print. `authentic` is the plain retail printing; it is shown to Vig as
  **Standard** everywhere in the UI (the JSON key keeps its original name).
  each print type (see "Print-type tracking / Missing-card tracking" below).
  There is no stored `missing` field any more: **missing is derived** =
  `count - (authentic+wc+proxy)`. `category` is one of
  `Pokemon`/`Trainer`/`Energy`. `image` is a pokemontcg.io URL; may be
  absent (shouldn't be, as of this writing — see "Current data state").
- `data/guides.json` — piloting-guide HTML per deck, keyed by
  `slug(deckName)` where `slug()` (defined identically in `index.html` and
  in the Python build scripts) lowercases, replaces every run of
  non-alphanumeric characters with `_`, and trims leading/trailing `_`.
- `data/turn1_rules.json` — turn-1 rules (coin flip + what the player
  going first can/can't do) keyed by the exact `year` label used in
  `cards.json` (e.g. `"2010"`). Rendered as an expandable
  box that only appears when a single year is filtered (never on "All
  years"). Hand-maintained, not generated — see `TURN1_RULES.md` for the
  research/sources and the "why" behind each entry. **If you add a new
  year to the collection, add a matching entry here too**, or the box
  just won't show for that year (silent, not an error — `renderTurn1Box()`
  in `index.html` treats a missing key the same as "All years").
- `data/games.json` — the **Game Log** backend: an array of played-game
  records, each `{date, year, myDeck, oppDeck, opponent, result, notes}`
  (`result` is `"Win"`/`"Loss"`/`"Tie"`; `year` is the format/collection
  year; `myDeck` is Vig's deck, `opponent` is who he played). Hand-maintained
  from what Vig reports in chat — there is **no live logging UI**; the Game
  Log tab only *displays* this file, with **Opponent** and **Year** filter
  dropdowns and a W–L–T + win-rate summary (win rate excludes ties). The
  table columns are Date / Year / Vig's Deck / Opponent's Deck / Opponent /
  Result / Notes. Loaded via its own guarded `fetch()` so
  a missing/empty file never breaks the site. Starts as `[]`.
- `data/inventory.json` — the **Inventory** backend: Vig's physical
  collection, one entry per card `{name, type, key, total, variants[]}` where
  each variant is `{version, set, num, qty, image}` (version = Standard /
  Reverse Holo / Prize Pack / Prize Pack Holo / Japanese / Full Art). `key` is
  the match key (see below). **This file is the source of truth** — it was
  seeded once from the "Collection" sheet of `PTCG Purchases Tracker.xlsx` by
  `scripts/build_inventory.py`, but is now hand-maintained from chat like
  cards.json; **re-running that importer overwrites hand edits**, so only do it
  on an explicit re-import request. Images are resolved at build time from the
  set code + number (PTCGO code → pokemontcg.io/scrydex id), so the page makes
  no API calls; ~21 brand-new cards have no image and render a placeholder.
  **Deck usage is derived live** in `renderInventory()`: `invKey()` (in
  index.html, mirroring `name_key()` in the scripts) is accent/case/punctuation-
  blind and strips "(variant)" tags and a leading "Basic ", so "Tapu Lele GX" ↔
  "Tapu Lele-GX" and "Basic Metal Energy" ↔ "Metal Energy" match. A card in no
  deck shows as **Spare**. This tab replaced the old deck-scoped "Card
  Collection" tab (removed).
  Every variant carries a **`source`**: `"Sheet"` (counted in the purchases
  spreadsheet) or a deck name (folded in from that built deck).
  **The spreadsheet only records recent purchases**, not the whole collection —
  older cards were already owned and were never entered. So the accounting is:
  `total owned = sheet copies + copies sleeved in pre-2026 decks`, and
  `spare = sheet copies - copies used by 2026 decks`. Pre-2026 deck copies are
  therefore ALWAYS added on top of the sheet (via
  `scripts/merge_deck_cards_into_inventory.py`, quantities from each deck's
  `prints`, missing excluded, one variant per deck/print-type); 2026 decks draw
  on the sheet stock and are NOT added again. (An earlier version wrongly
  skipped any card already in the sheet — that made Zacian V read 1 when five
  2020-2023 decks held 11 more; it should read 12 with 1 spare.) The merge
  script strips previously-merged deck variants first, so it is safe to re-run.
  **Display groups by print, not by row.** `renderInventory()` buckets a card's
  variants by `set + num` first, because two prints are genuinely different
  cards (Azelf LA 19 vs Azelf MT 4 must never interleave). Print *type*
  (World Champs / Standard / Proxy / Reverse Holo...) is a separate
  axis, so all types of one print sit under a single heading with the deck
  holding each — e.g. Ultra Ball SVI 196 shows its WC and Standard copies
  together. Variants with no set recorded collect under "Set unknown" at the
  bottom, pending Vig's physical check.
  **Verification tab: print make-up per deck.** Each row carries a proportional
  strip plus a one-word verdict — **Standard / WC / Mixed** — so a glance says
  whether a box is all World Champs, all retail, or a blend. The strip uses the
  DECK-LIST pip colours (green Standard, grey WC, blue Proxy, faint Missing), so
  it matches what the expanded deck shows; hovering gives exact counts. Vig had
  the "checked" / "N of M left" text removed on 2026-08-25 -- the bar and the
  make-up strip is all he wants on a deck row -- the green progress bar went too.
  A deck row is now just name + strip + word; the green deck name still marks a
  checked box, and exact counts live in the strip's tooltip. Only the Loose stock
  row keeps a progress bar and text label, since that phase is still running. It reads
  `prints` off `cards.json`, the same source as the pips, which means an
  unverified deck shows its recorded-but-unconfirmed make-up. On phones the
  strip, word and bar all narrow so long deck names keep their full width.

  **Three count pills per row.** The Inventory row's copy count splits into
  **Standard (red) · World Champs (blue) · Proxy (grey-violet)**. Standard means
  every real retail finish — plain, Reverse Holo, Holo, Prize Pack, Full Art,
  Japanese — so only an actual Proxy leaves that pill. Vig asked for this on
  2026-08-25: proxies had been folded in with Standard, which overstated how
  many real cards a row held (Shaymin-EX ROS 77 read 6 retail when it is 2 plus
  4 proxies). Any pill is omitted when it would read zero. Note the colours do
  NOT match the deck pips, where WC is grey and blue means Proxy — Vig asked for
  blue=WC here specifically.

  **Stand-in images.** Some prints have no catalogued picture anywhere: the
  Japanese-only sets (M2a/M3/MEP/s12a), the BW Trainer Kit (`BWTK`), basic
  energies printed without a collector number (`SSH`, `TEU`, unnumbered `SUM`),
  and **`MEE`**, the Mega-Evolution-era energy set, which the card API does not
  carry at all (its Scarlet & Violet counterpart `sve` exists; the ME one does
  not). MEE rows are numbered 1-8 exactly as SVE is -- Grass, Fire, Water,
  Lightning, Psychic, Fighting, Darkness, Metal -- and borrow that same energy's
  SVE artwork.
  Those rows borrow another print's image, and carry a **`standIn`** string
  saying so. The Inventory row shows a small "stand-in image" chip and the card
  modal prints the reason underneath — without it the site quietly presents a
  different card as though it were this one. Set `standIn` whenever an image
  does not depict the actual card; clear it when a real one becomes available.

  **Promo and prize stampings go on the `version`.** A card that shares its
  number with the ordinary print but carries a stamp -- OCIC Promo, League
  Promo, Prerelease Promo, "2nd Place League Challenge" -- is recorded as its
  own variant on the same row, so it reads as a separate line rather than
  merging with the plain copies (Vig asked for this on 2026-08-30). `version` is
  free text; only "World Champs" and "Proxy" are special-cased by the UI, so any
  other label counts toward the Standard pill, which is correct for a promo.

  **A card subbed in for a different card is NOT a Proxy version.** Vig was
  explicit on 2026-08-25: a stand-in is an ordinary card being played in another
  card's slot, so the inventory `version` stays **Standard** (or whatever finish
  it actually is). "Proxy" as a *version* is reserved for a copy that is not a
  real card. The substitution is a fact about the DECK, and lives on the deck
  row's `prints.proxy` -- which is why `align_deck_prints.py` only ever raises
  that count, never lowers it. Mega Rayquaza (2017) is the worked example: it
  sleeves Air Balloon ASC 181, N's Plan BLK 83 and Professor Juniper PLB 84 for
  Float Stone, N and Professor Sycamore. All three are Standard in the inventory
  (the same rows are the genuine card in other decks -- Air Balloon really is
  Air Balloon in Alakazam), while the decklist keeps naming the real card and
  shows blue proxy pips. **`PROXY_SUBS`** in `scripts/audit_inventory.py` maps
  `(deck, inventory key) -> decklist key` so the deck-claim check still balances;
  add an entry there for every new substitution, and pin the deck/card in
  `align_deck_prints.py` so the displayed print is never rewritten.

  **Explicit deck assignments + verification (Vig's ongoing pass):** he is
  working through the collection telling me which physical copies sit in which
  deck (e.g. "Dreepy: 4 Reverse Holo PRE 71 are in Dragapult Dusknoir (2026),
  4 in Dragapult (2026)"). Record that by setting the variant's `source` to the
  deck name (splitting a variant row if only some copies are assigned). A
  variant sourced `"Spare"` is loose stock, and only assumes a
  current-format deck is drawing on that pile when no variant already names
  that deck — so assignments make the spare count exact.

  **Verification is per STACK, not per row.** A "stack" is one variant: one
  deck's copies of one print, e.g. the 4 World Champs Iono PAL 185 in
  Dragapult (2025). Set `"verified": true` on the variant when Vig has that
  box open and confirms it. The flag used to sit on the row, but a row is
  shared — Iono PAL 185 is held by nine decks — so checking one box wrongly
  marked the other eight and silently cleared their checklists. Migrated by
  `scripts/migrate_verification.py`, seeded from the boxes actually opened
  (2025 + 2026). Earlier auto-verify passes were deductions from Vig's bulk
  print rules, not cards anyone looked at, so they did NOT carry over.

  A row's marker is derived: ✓ every stack checked, ◐ some, • none. Each stack
  line carries its own ✓/•. Filters are "Verified" / "Partly verified" /
  "Not verified yet"; the stats line counts stacks (e.g. `370/2202`).

  **The Verification tab** (Tools) is the progress view: decks checked, deck
  stacks, spare stacks, and a per-deck bar grouped by year. The order of work
  is all decks first, then the spare boxes.

  **The old spare figures were cleared on 2026-08-30.** They were never
  observed -- `spare = sheet copies - deck copies` -- and the deck pass had just
  corrected ~200 prints in that same sheet, while anything never on the sheet
  was absent entirely. 149 stacks / 293 copies sit in
  `data/archive/spares_2026-08-30.json`, and Vig is entering the loose boxes
  from the cards themselves.

  **Do not diff the new count against that archive.** An earlier note here said
  to; Vig ruled it out on 2026-08-30 -- "that was a made up number all along".
  The archive is a record of what was removed, not a baseline, and gaps against
  it mean nothing. The physical count is the only truth about the spare boxes;
  do not quote 293, or any figure derived from it, as a benchmark.

  **The Inventory no longer infers anything about spares.** It used to assume a
  current-format deck short of a card was drawing on loose stock and quietly
  subtract those copies from the spare count (`invAllocate`, removed
  2026-08-30). With every deck verified card by card that assumption is simply
  wrong, and it was hiding three real spares by showing them as sleeved. Spare
  count is now just the copies sourced `"Spare"`, and the per-row deck list is
  gone because every deck holding a print is already named on its variant line.

  **Never move a spare into a deck on your own initiative.** A loose copy of a
  card a deck is short is a common and unremarkable state -- Vig owns the card,
  it just is not sleeved. He said on 2026-08-30 that he will say explicitly when
  a card moves from a spare box into a deck. Report the overlap if it is worth
  knowing, but leave the stack sourced to `"Spare"` until he says otherwise. Deck stacks were untouched (2084/2084 still verified). The old
  order of work was — once every deck has claimed its
  copies, whatever is still `"Spare"` is what is physically loose.
  2026 decks stay display-only — deck `prints`/missing markers are never
  rewritten from inventory. Vig intends to walk through the deck-sourced
  entries and correct the numbers over time.
- `scripts/audit_inventory.py` — **run this after every single change to
  `data/inventory.json`, without being asked.** Vig's instruction: keep the
  inventory clean as you go rather than waiting to be reminded. It checks row
  totals against their stacks, card numbers that still carry the printed total
  ("58/202"), missing images that can be derived, stale `printKey`s, duplicate
  stacks on a row, two rows for one print, stacks with no version or an unknown
  deck, empty rows, and every deck holding exactly what it plays. `--fix`
  repairs the safe ones and rewrites the file sorted; it exits non-zero while
  anything is unresolved, so it can gate a commit. Every check is there because
  that fault actually occurred — most were spotted by Vig on the site, which is
  the thing this script exists to prevent.
- `scripts/export_xlsx.py` — exports everything to one .xlsx (Inventory / Decks
  / Cards to Get / Tournaments / Summary sheets). Run it whenever Vig wants a
  spreadsheet copy back out; that's the agreed replacement for maintaining the
  xlsx by hand.
- `data/tournaments.json` — the **Tournament Log** backend: an array of events,
  each `{name, type, date (YYYY-MM-DD), deck, players, record, placement, notes,
  list}`. `record` is `{wins,losses,ties}` (Pokémon W-L-T convention) or `null`
  = TBD; `placement` is Vig's finishing position (shown as `placement / players`)
  or `null`; `list` is the raw decklist text played (kept verbatim, shown
  preformatted with a Copy button). Hand-maintained from chat — **no logging UI**,
  the tab only displays. The **Standard format is computed from `date`** by
  `formatForDate()` in `index.html`: `STD_SETS` (SV+Mega set release dates) +
  `STD_ROTATIONS` (season-start → earliest legal set) give the legal span
  (e.g. 2026-08-24 → "Temporal Forces – Pitch Black", 16 sets). **Add a new
  `STD_ROTATIONS` entry when a real rotation drops a set**, and extend `STD_SETS`
  as new sets release. Loaded via guarded `fetch()`; starts `[]`.
- **Tools tab is private/gated.** The `Tools` top tab (`data-tab="tools"`,
  holding Inventory / Cards to Get / Tournament Log / Stats, in that order;
  Matchup Generator and Game Log are parked behind a `hidden` attribute on
  their sub-tab buttons — their panels and code are untouched, so removing
  `hidden` switches either back on) is `hidden` by default so public visitors (and the printed-QR URL,
  which must stay untouched) never see it. `applyToolsGate()` in `index.html`
  reveals it only when unlocked: (a) launching from the **home screen** —
  `isStandaloneApp()` (navigator.standalone / display-mode:standalone) — always
  shows Tools, since an install is intentional and this side-steps the iOS
  web-clip storage sandbox; or (b) in Safari, visiting `#tools` once sets a
  `toolsUnlocked` localStorage flag (remembered per device) and the tab then
  shows even on the plain URL; `#lock` clears it. The unlock word is
  `TOOLS_KEY` in `applyToolsGate()`. The head opts into standalone via
  `apple-mobile-web-app-capable`/`mobile-web-app-capable` and the manifest is
  `display:standalone` with `start_url:"index.html#tools"` (belt-and-suspenders).
  This is convenience, not security — a static page's source is always readable. Runs on load and on `hashchange`,
  and wipes the key from the address bar via `history.replaceState`.
- **Matchup Generator tab** — the default sub-tab of the Tools tab (`#matchupTab`,
  alongside `#collectionTab`) with no separate data file; it reads
  directly from the already-loaded `CARDS` array. Pick a format (or leave
  it on "Random format") and click "Randomize Matchup" to get two
  distinct random decks from that format (`pickTwo()` in `index.html`).
  Re-clicking the button keeps whatever format is currently selected in
  the dropdown — it only re-rolls the format too if the dropdown is still
  on "Random format". Clicking either deck name in the result jumps to
  the Collection tab with that deck's year filtered and its name typed
  into the search box (reuses the existing search/filter machinery rather
  than adding new deck-lookup logic — see `jumpToDeck()`).
- `apple-touch-icon.png` (180) / `icon-192.png` / `icon-512.png` +
  `manifest.webmanifest` — home-screen / PWA icons (iOS ignores the inline SVG
  favicon for home-screen web-clips, so a real PNG is required). All three PNGs
  are generated from the favicon's pokeball artwork by `scripts/make_icons.py`
  (Pillow); re-run it if the pokeball ever changes. iOS caches the icon hard —
  after adding it, an already-saved home-screen bookmark must be removed and
  re-added to pick it up. `manifest.webmanifest` uses `display:browser` and
  `start_url:"."` so it stays a normal bookmark on the QR-safe plain URL.
- `piloting_guides_collection/<year>/*.md` — source markdown for every
  guide, one file per deck. **Edit these, not `data/guides.json` directly**
  — the JSON is generated output.
- `Old_Format_Collection_20102025.xlsx` — the original spreadsheet the card
  data was first compiled from. Not read by anything anymore; kept for
  reference. `data/cards.json` is now the actual source of truth for card
  data — edit it directly, or add rows via a script (see below).
- `card_collection_with_urls.csv` — Name/Set/Set Code/Image URL for known
  card prints. This is what `scripts/merge_image_urls.py` joins against.
  **This CSV is unreliable on its own — see "Bugs found" below.**
- `scripts/` — Python, needs the project's `.venv` (see Setup below):
  - `extract_cards.py` — one-off, historical. Pulled the original card
    data out of the v1 prototype's inline HTML. Never needs to run again.
  - `categorize_cards.py` — assigns `category` to every row in
    `cards.json`. Rerun after adding new card names.
  - `merge_image_urls.py` — assigns `image` to every row in `cards.json`
    by joining `card_collection_with_urls.csv` on `(name, set)`. Rerun
    after adding new cards, or after adding entries to `URL_OVERRIDES`.
  - `build_guides.py` — regenerates all of `data/guides.json` from the
    markdown source. Rerun after editing any guide `.md` file.
  - `update_cinccino_mill_2020.py` — one-off, historical (see "Bugs
    found"). A template for how to bulk-replace one deck's card list if a
    future correction is needed: build a `NEW_ROWS` list of
    `(count, name, set)` tuples, filter out the old deck's rows, extend,
    assert the total is 60, write back.

### Setup (first time in a new session/machine)

```bash
cd pokemon-old-format-collection
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`.venv/` is gitignored. `requirements.txt` currently just pins `markdown`
(used by `build_guides.py` to convert guide `.md` → HTML with the `extra`
extension, which is what gives tables/fenced-code/etc. — plain
`markdown.markdown(text)` without `extensions=['extra']` produces
different, less complete HTML).

### Local preview

`index.html` needs http(s), so serve the folder, don't open the file
directly:

```bash
python3 -m http.server 8080   # from the repo root, then visit localhost:8080
```

## Updating the collection next year (or anytime)

### If Vig gives you a new deck + guide

Ask him for, in this order (he's given all of this before without being
asked in detail, but confirm you have it):

1. **The decklist**: a table/CSV with columns Year, Deck (exact display
   name, e.g. `"Some Deck (2026)"`), Qty, Card Name, Card Number
   (`"145/147"` format, or blank for basic Energy). He's supplied this as
   a pasted markdown table before — that's fine, just extract it.
2. **The guide**: either a `.md` file (he's attached files directly
   before, e.g. `@"/Users/.../Cinccino Mill 2020 updated decklist.md"`)
   or ask him to write/paste one. Match the existing guide format exactly
   (see any file under `piloting_guides_collection/` for the template:
   H1 title `# How to Pilot — <Deck> (<Year>)`, italic format blurb, then
   `## One-line identity`, `## The meta it lived in`, `## Engine cards...`,
   etc. — copy the section headers from a recent guide rather than
   inventing your own structure).
3. **Image URLs for any new/unusual cards** — see below. Don't assume the
   CSV or an AI-guessed URL is correct; verify with `curl -s -o /dev/null
   -w "%{http_code}"` before adding to data.

Then:

```bash
# 1. Add the card rows to data/cards.json (write a small one-off script
#    like scripts/update_cinccino_mill_2020.py, or edit the JSON directly
#    if it's a small number of rows — it's just an array of
#    {year, deck, count, name, set} objects, no other structure).

# 2. Save the guide .md under piloting_guides_collection/<year>/, then:
.venv/bin/python scripts/build_guides.py

# 3. Categorize any new card names (see "Card categorization" below):
.venv/bin/python scripts/categorize_cards.py
#    -> if it errors ("computed slug doesn't match any deck"), that means
#       a name in cards.json changed but categorize wasn't told - check
#       ENERGY_NAMES / TRAINER_NAMES for typos or missing entries.

# 4. Merge image URLs:
.venv/bin/python scripts/merge_image_urls.py
#    -> reports how many rows got an image and how many didn't. If a
#       new card has no image, either it's genuinely not in the CSV
#       (add to URL_OVERRIDES after verifying) or the name doesn't match
#       the CSV's spelling (add to NAME_FIXES).

# 5. Test locally (see "Local preview" above), then check the new deck
#    renders, sections group correctly, guide opens, images load.

# 6. git add -A && git commit -m "..." (see "Git & pushing" below)
```

### One line per card in a decklist

A deck's card list shows **one row per card name**, never one row per printing.
When Vig's physical check turns up two prints of the same card in a box — 3
Great Ball SLG 60 and 1 SUM 119 — the deck row stays a single `4x Great Ball`
carrying the majority print, and the split is recorded in `data/inventory.json`
as separate stacks. That is his stated preference: the list reads tidily, the
inventory carries the reality.

Vig's rule for a name appearing on two rows of one deck is **by category**:

- **Trainer or Energy** — always one line. It is a reprint; merge it.
- **Pokémon** — nearly always two genuinely different cards sharing a name, so
  leave it split and **ask him** how he wants it shown rather than guessing.
  Confirmed different: Garbodor GRI 51 (Trashalanche) vs BKP 57 (Garbotoxin),
  Inteleon SSH 58 (Shady Dealings) vs CRE 43 (Quick Shooting), Kirlia, Ralts,
  Azelf, Hoppip, Marshadow, Greninja. The exception already merged is Shadow
  Rider Calyrex V, where CRE 74 and the SWSH131 promo really are one card.

`align_deck_prints.py` applies exactly this: it merges Trainer/Energy duplicates
and prints Pokémon ones for Vig to rule on. Checking abilities/attacks via the
card API settles any case that is unclear.

`scripts/align_deck_prints.py` enforces this. For every **fully verified** deck
it compares each deck row against the prints the inventory says that box holds,
and rewrites the row's `set`/`image` to the majority print (`--fix`). Run it
after verifying a box. It deliberately leaves alone:
- **basic energy** — a decklist keeps an empty `set`, which is also the key
  `merge_image_urls.py` uses for its `URL_OVERRIDES`; give one a real set number
  and that script deletes the image on its next run;
- **Japanese-only sets** (M2a, M3, MEP, s12a) — Vig's rule: the decklist shows
  the **English** print's set number and image, and the Japanese card is tracked
  only in the inventory. The inventory row keeps its Japanese `set`/`num` but
  carries an English stand-in `image`, so clicking it shows the same picture the
  decklist does. Where a row serves one deck, match that deck's English print
  exactly; a row shared by several decks (Fezandipiti ex M2a 114 sits in four)
  can only pick one, so any valid English print of the card is fine. The audit
  flags a Japanese row with no stand-in image;
- **exact ties** (2 of one print, 2 of another) — one is simply picked: the row
  keeps what it already shows if that is one of the tied prints, otherwise the
  first by set/number, so the choice is stable rather than flipping each run;
- **unverified decks** — their inventory is still inference, so it has no
  authority over the list.

### TODO — basic energy prints not yet identified

Vig is identifying which printing of each basic energy sits in each box as he
works through the years. **47 stacks across 29 already-verified decks predate
that**, so they carry no print. He has parked these deliberately: finish the
remaining years first, then revisit
these boxes. Do not chase him for them before then. **The years still to
verify are 2019, 2018, 2017, 2016 and 2014** — 2013 and 2015 have since been
done. The loose/spare boxes come after all of it; Vig reconfirmed that ordering
on 2026-08-25.

Two shapes, both of which `align_deck_prints.py` leaves off a decklist:

- **`XY` placeholder row, no card number** — print genuinely unknown. This is
  the merge script's stand-in for "a basic energy, printing not recorded", and
  is what all of 2010 / 2022-2025 still uses.
- **A set but no card number** — SWSH-era basic energies are printed *without*
  a collector number. **Settled 2026-08-22: these show the set code alone**, so
  the line reads `SSH`. Done for ADP Zacian, Ice Rider, Shadow Rider and
  Spiritomb. The card API has no image for an unnumbered SWSH basic, so those
  rows keep the XY basic-energy art they already carried.
- **No set at all** — the nine 2026 decks, whose basics were never asked about.

Decks affected:

```
  ADP Flying Pikachu (2022)    3x Fighting Energy, 4x Lightning Energy
  ADP Zacian (2020)            8x Metal Energy, 2x Water Energy
  Alakazam (2026)              1x Psychic Energy
  Ancient Toolbox (2024)       6x Darkness Energy
  Boltevoir (2010)             1x Fighting Energy, 5x Psychic Energy
  Charizard Pidgeot (2025)     6x Fire Energy
  Cynthia's Garchomp (2026)    4x Fighting Energy
  Dragapult (2025)             1x Fire Energy, 2x Psychic Energy
  Dragapult (2026)             2x Darkness Energy, 3x Fire Energy, 4x Psychic Energy
  Dragapult Dusknoir (2026)    2x Darkness Energy, 3x Fire Energy, 3x Psychic Energy
  Gardevoir (2023)             10x Psychic Energy
  Gardevoir (2025)             4x Darkness Energy, 7x Psychic Energy
  Hide 'n' Sneak (2026)        2x Psychic Energy
  Ice Rider (2021)             8x Water Energy
  Ice Rider Palkia (2022)      8x Water Energy
  Iron Thorns (2024)           7x Lightning Energy
  Joltdengo (2025)             4x Grass Energy, 4x Lightning Energy, 3x Metal Energy
  Jumpluff (2010)              6x Grass Energy
  Lost Box Kyogre (2023)       3x Lightning Energy, 3x Psychic Energy, 5x Water Energy
  LuxChomp (2010)              2x Lightning Energy, 2x Metal Energy
  Miraidon (2024)              16x Lightning Energy
  N's Zoroark (2026)           7x Darkness Energy
  Raging Bolt (2025)           3x Fighting Energy, 6x Grass Energy, 3x Lightning Energy
  Regidrago (2024)             3x Fire Energy, 7x Grass Energy
  Rocket's Mewtwo (2026)       6x Grass Energy, 1x Psychic Energy
  Shadow Rider (2021)          14x Psychic Energy
  Slowking (2026)              4x Psychic Energy
  Spiritomb (2021)             3x Darkness Energy
  Urshifu VMAX (2022)          3x Fighting Energy
```

When picking this back up, a compact energy-only checklist is enough — the rest
of those boxes is already verified.

### Deck ordering (alphabetical — automatic)

Decks are **always shown alphabetically** (case-insensitive), and this is
enforced at render time in `index.html`'s `render()`, not by the row order
in `cards.json`. So a newly added deck sorts into place on its own — you do
**not** need to insert its rows at any particular position in `cards.json`,
and you must not reintroduce manual ordering there. The sort is two-level:
years stay in chronological order (via the `YEARS` array, so "All years"
still reads oldest→newest; a same-year labelled event like a future
`2018 NAIC` would sort just before its bare year), and within each year
the decks are alphabetical by display name. Filtering
to a single year therefore shows a purely alphabetical list. If you add a
whole new *year*, it slots in via `YEARS`; nothing about the deck sort
needs changing.

### Print-type tracking / Missing-card tracking

Every owned copy is one of three print types, tracked per row in
`prints:{authentic, wc, proxy}` (World Championships / Proxy). The invariant
is `authentic + wc + proxy <= count`; the leftover, **`count - sum`, is what
Vig is Missing**. There is no separate `missing` field — it's always derived.
All existing owned copies were seeded to `authentic` on 2026-08-15; Vig
dictates the exceptions in chat and I hand-edit `cards.json`:
- *"Sycamore: 2 WC, 1 Standard, 1 Proxy"* (count 4) → `prints:{authentic:1,
  wc:2, proxy:1}` (missing 0).
- *"2x Pidgey missing"* (count 2, was all authentic) → `prints:{authentic:0,
  wc:0, proxy:0}` (missing 2). Marking missing = **lower the owned buckets**
  so the leftover grows; un-marking = raise `authentic` back up.
- Basic energy (empty `set`, category Energy) is always a single print type,
  never a mix.
The regen scripts (`categorize_cards.py`, `merge_image_urls.py`) preserve
`prints` — they only touch `category`/`image`. If you bulk-replace a deck's
rows, its `prints` are lost unless re-added; new rows default to
`{authentic:count, wc:0, proxy:0}`.

`index.html` renders per-copy **pips** in the expanded deck view only
(collapsed rows untouched), ordered **Standard (green) → WC (grey) → Proxy
(blue) → Missing (dashed red)**. There is **no legend row** — Vig had it
removed on 2026-08-25 as self-evident; the copy-decklist button that shared
that row now lives in `.deck-head .meta`, so it costs no vertical space and
works while the deck is collapsed. On mobile the count pill drops its " cards"
word (`.cb-unit`) to buy back the width the button takes, which otherwise
ellipsed the longest deck names. Pokémon/Trainers/special energy show one pip per copy; basic
energy collapses to `count + one pip` per bucket. Helpers `printsOf(c)` /
`missingOf(c)` (in `index.html`) are the single source for missing math.
The **"⚠ Missing" toggle** (`missingOnly` in `render()`) filters to rows with
`missingOf(c) > 0` and **stacks with the year chips** (e.g. 2021 + Missing);
the deck header pill still shows the owned count / "N missing" and tints
(`has-missing`). Pip colors are the `--pip-*` CSS vars (dark mode overrides
`--pip-wc`/`--pip-proxy`). The old per-row orange/red tint + "missing N of
count" badge were **replaced** by the dashed pips (that CSS is now dead but
left in place).

### Favourite deck of the year (star icon)

Vig's favourite deck of each year shows a gold **star-with-pokéball** icon
next to its name in the All Decks list. The picks are a hardcoded
`FAVOURITES` Set of exact deck names in `index.html` (not in cards.json) —
edit that set to change a pick. The icon is an inline SVG constant
(`FAV_STAR`) rendered into the deck header when `FAVOURITES.has(deck)`; it's
drawn from scratch (the source was an attached PNG that couldn't be embedded
as bytes), so tweak the SVG if a closer match is ever wanted. Currently one
per year, 2010–2025.

### Card categorization (Pokemon / Trainer / Energy)

There is **no type/category column anywhere in the source data** — not in
the original xlsx (checked every sheet: Home, Template, per-year sheets,
MasterTable — all just Year/Deck/Count/Name/Set), not in the CSV. Category
is assigned by explicit, hand-verified name lists in
`scripts/categorize_cards.py`:

- `ENERGY_NAMES` — exact card names that are Energy cards.
- `TRAINER_NAMES` — exact card names that are Trainer cards (Items,
  Supporters, Stadiums, Tools — all one bucket, no further subdivision).
- Anything **not** in either list defaults to `"Pokemon"`.

This default-to-Pokemon approach is deliberate and safe: Trainers and
Energy are closed, well-known vocabularies (maybe a few hundred names
total across the game's entire history), while Pokémon species/forms are
not enumerable up front. When you add a new deck, any brand-new Trainer or
Energy card name needs a line added to the relevant list, or it'll
silently (and wrongly) categorize as Pokemon. `categorize_cards.py`'s
`main()` doesn't currently warn about likely-miscategorized entries beyond
the slug-mismatch check — after running it, it's worth eyeballing
`Counter(c['category'] for c in cards)` for a sudden count shift, or
grepping the printed category counts against what you'd expect (67 decks
× ~7-8 Pokemon/~13 Trainer/~2 Energy average lines, per deck, is the
existing baseline).

### Image URLs

`scripts/merge_image_urls.py` joins `card_collection_with_urls.csv`
(columns: Name, Set, Set Code, Image URL) onto `cards.json` by exact
`(name, set)` match, with two escape hatches:

- `NAME_FIXES` — normalizes spelling variants (mojibake, missing accents,
  doubled spaces) so a row isn't missed just because the CSV spelled that
  print's name slightly differently than `cards.json`.
- `URL_OVERRIDES` — hand-verified `(name, set) -> URL` pairs for cards the
  CSV never resolved at all (or resolved to a placeholder — see "Bugs
  found"). **Every URL in this dict was checked with a live HTTP request
  before being added — do the same for any new entry.** A quick way to
  batch-verify:
  ```bash
  cat urls.txt | xargs -P 20 -I{} sh -c \
    'code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "{}"); \
     [ "$code" != "200" ] && echo "$code {}"'
  ```
  (empty output = everything resolved). This was run against all ~700
  unique image URLs in the collection as of this writing and all passed.

Basic Energy (Grass/Fire/Water/Lightning/Psychic/Fighting/Darkness/Metal/
Fairy) is recorded in `cards.json` with an **empty string** for `set`
(decklists don't note which printing of a basic Energy was used). All 9
are pinned via `URL_OVERRIDES` to their XY base-set printing (`xy1`,
cards 132–140/146) as a consistent representative image — this was Vig's
explicit choice, not a default worth silently changing.

### Guide-to-deck slug matching

The site matches a deck's card list to its guide via
`slug(deckName) === slug(guide's own key in guides.json)`. Almost every
guide file's H1 title matches its deck name in `cards.json` exactly (after
slugifying), **except one**, hardcoded in `build_guides.py`'s
`MANUAL_SLUG_OVERRIDES`:

- `Perfection_Mewtwo_2019.md` (titled "Perfection (Mewtwo & Mew-GX)
  (2019)") → deck `"Perfection Mewtwo (2019)"`

(There used to be three. `Blacephalon_GX_2019.md` and
`Greens_ReshiZard_2019.md` stopped needing an override once their decks
were renamed to `"Blacephalon GX (2019)"` and `"Green's Reshizard (2019)"`
— the titles now slugify to the deck names on their own. Note the two
**filenames** still use the older spelling; only the H1 and the deck name
have to agree, so renaming the files was unnecessary churn.)

If you add a new guide whose title doesn't match its deck's exact name in
`cards.json`, add an entry here rather than renaming either side — the
mismatches above are intentional (the guide title is more descriptive
prose, the deck name is the terse spreadsheet-style name).

### Git & pushing (important environment quirk)

**Claude Code's Bash tool in this environment has no TTY** — it cannot do
an interactive credential prompt or browser-based OAuth flow. `git push`
over HTTPS fails immediately with `could not read Username for
'https://github.com': Device not configured`. There's no `gh` CLI and no
SSH key set up on this machine as of this writing.

The working pattern, established with Vig:

1. Commit locally as normal.
2. Ask Vig for a fresh GitHub Personal Access Token (classic, `repo`
   scope) when ready to push.
3. Push with the token **inlined in a one-off URL**, never via `git remote
   set-url` or `git push -u` with the token embedded — either of those
   writes the token straight into `.git/config` in plaintext:
   ```bash
   git push "https://<token>@github.com/vmurthy45/PTCGOldFormatCollection.git" main:main
   ```
4. Immediately verify the token didn't leak to disk: `grep -i ghp_
   .git/config` should print nothing.
5. Tell Vig it's safe to revoke the token now (it was pasted in chat, so
   treat it as compromised the moment it's served its purpose regardless).
6. GitHub Pages' CDN takes roughly 60–90 seconds to pick up a new push —
   don't panic-report stale data as a bug if you check immediately after
   pushing; wait (via `ScheduleWakeup` or similar) and recheck.

This happened twice in development (a token got written to `.git/config`
once via `git push -u` before the pattern above was established — caught
and fixed with `git fetch origin && git branch -u origin/main main`,
which repoints tracking without needing another push).

## Bugs found during development (don't reintroduce these)

1. **CSV placeholder values treated as valid URLs.** For a printing it
   couldn't resolve, `card_collection_with_urls.csv` doesn't leave the
   Image URL blank — it puts the literal string `"Not Found"` or `"Error"`
   in that column. An early version of `merge_image_urls.py` did
   `if url: c['image'] = url`, and since those strings are truthy, 26 rows
   ended up with `"image": "Not Found"` — a broken image that *looked*
   matched in the script's own success-count output. Fixed by requiring
   `r["Image URL"].startswith("http")` before accepting a CSV row's URL as
   real. **Lesson: when a script reports "matched N/M", verify what "matched"
   actually means for the data, don't just trust the count.**

2. **Stale README numbers.** The `piloting_guides_collection/README.md`
   that shipped with the original content said "65 guides" and listed only
   2 of the 4 planned 2025 decks — but the other 2 guide files already
   existed and were fully written; the README was just never updated after
   they were finished. Always cross-check a README's claimed counts
   against `find ... -name '*.md' | wc -l` rather than trusting prose.

3. **Card name spelling inconsistency.** The same physical card appears
   under multiple spellings across the data: `"Pokemon Collector"` /
   `"Pokémon Collector"` / `"Pokemon  Collector"` (double space), plus one
   literal mojibake string `"Pok√©mon Catcher"` (UTF-8 bytes misread as
   Latin-1 at some point upstream). This breaks exact-match joins (image
   lookup) and category lookups silently. Handled via `NAME_FIXES` dicts
   in both `merge_image_urls.py` and (implicitly, by listing both spellings)
   `categorize_cards.py`. If you hand-edit `cards.json` and introduce a new
   spelling of an existing card, this class of bug will resurface —
   grep for the card name across the file first.

4. **v1 prototype's embedded content was incomplete.** The very first
   version of this site (built in an earlier chat session, before this
   repo existed) had all 65-67 guides *intended* to be inline in
   `index.html`'s JSON blob, but only 5 were actually embedded. Don't
   trust a predecessor's self-description of its own completeness —
   verify against the actual file/data.

## Vig's preferences (confirmed via explicit feedback, not assumptions)

- **Light mode is the default** (set 2026-08-22). The site used to follow
  `prefers-color-scheme`, so a dark OS produced a dark site nobody asked for.
  The toggle still works and is remembered, under the key `themeChoice`; the
  old `theme` key is deleted on load and ignored, because the previous code
  wrote it on *every* load — a saved `dark` there could not be told apart from
  a real choice, so keeping it would have pinned returning visitors to dark
  forever. Only an actual click on the toggle persists anything now.
- **Dark mode = background only.** He explicitly rejected a gradient
  header/deck-bar treatment and a shifted (brighter) red accent for dark
  mode, and asked for the exact same colors/icons as light mode, with only
  the background/surface colors actually changing for dark. The one
  deliberate exception: `--charcoal`/`--charcoal-dark` (guide-content
  heading/bold text color) still flips per-theme, because pinning it to
  the light-mode value makes that text unreadable on the dark card
  background — this was a judgment call, explained to him, not silently
  overridden. If asked to touch theming again, preserve this: same accent
  red and pokéball icon in both themes, dark mode only changes bg/card/
  border/badge colors.
- **Wants exact capitalization/wording checked**, e.g. corrected "how to
  pilot this deck" → "See Guide" (capital G) when first implemented
  lowercase.
- **Wants rigor on "is anything broken" questions** — when asked "are any
  images not working," he wanted an actual HTTP check of every URL, not
  just "no rows are missing an image." Default to verifying with a real
  request when the question is about whether something works, not just
  whether data is present.
- **Supplies corrections iteratively and expects them applied precisely**
  — e.g., a corrected decklist for one specific deck, a specific missing
  image URL for one specific card. Don't over-generalize a fix beyond what
  was asked (e.g., when given an Air Balloon URL for print 156/202, that
  was applied only to that print, not used to overwrite the *different*,
  already-correct Air Balloon 79/86 print elsewhere in the data).
- **Fine with git commits happening without asking each time** once a
  logical unit of work is done, but has explicitly wanted to control the
  *push* step himself (providing tokens one at a time, confirming revoke).
  Keep committing locally proactively; keep gating the actual push on him
  supplying a token.
- Uses GitHub username `vmurthy45`. Prefers not to install extra tooling
  (`gh` CLI) — declined that option early on in favor of the manual-token
  push pattern above.

## Current data state (as of the last update in this file)

- 86 decks, 2043 card rows, 16 "formats" (year groupings, 2010–2026 with
  no 2011). The one-time standalone `2017 NAIC` label was consolidated into
  `2017`: its four decks moved to 2017. Three took World-Championship-format
  lists (Guzma over Lysandre, Burning Shadows legal): Tapu Bulu Vikavolt,
  Espeon Garbodor, and Decidueye (→ Decidueye Ninetales, reusing the old
  guide with Lysandre→Guzma). The fourth, Zoroark Drampa, was reinstated
  as **Drampa Zoroark (2017)** with its original BKT-Zoroark-BREAK list —
  which still runs Lysandre (all cards legal in the 2017 season); its guide
  keeps the original text with the card mechanics corrected against the API
  (Mind Jack is 10+30×bench, Berserk keys off your own damaged bench).
- Every row has a `category`. Every row has an `image` — 780 unique image
  URLs, all verified HTTP 200. **Almost all are `images.pokemontcg.io`; the
  exception is three cards in Rocket's Honchkrow (2026) from the newest
  Mega-era sets (me2pt5 "ASC", me3 "POR") which pokemontcg.io doesn't host
  yet — those use `images.scrydex.com` URLs (the only source, verified 200).
  If pokemontcg.io later adds them, they can be repointed.**
- All 76 piloting guides exist and are wired up (`data/guides.json` has 76
  keys, one per deck). Three are intentional "TBC" stubs whose decklists are
  complete but write-ups aren't: **Eternatus VMAX (2021)**, **Rocket's
  Honchkrow (2026)**, and **Cynthia's Garchomp (2026)**. Every other deck has a full guide.
- `data/turn1_rules.json` has an entry for all 15 year labels.
- 2021 uses the **Players Cup III/IV** online events as its benchmark
  (there was no 2021 Worlds — COVID). Lists came from the Limitless
  tournament archive (`limitlesstcg.com/decks/list/<id>`), whose HTML
  carries `data-set`/`data-number` attributes that map cleanly onto
  pokemontcg.io image URLs — a useful trick if more archived lists are
  ever imported.

If any of these counts don't match what you find when you pick this
project back up, something changed (Vig added/edited a deck) — that's
expected and fine, just don't assume this doc is still 100% current on
specifics; treat the numbers above as "last known good," and the
*process* described above as the durable part.
