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
  `{year, deck, count, name, set, category, image}`. `category` is one of
  `Pokemon`/`Trainer`/`Energy`. `image` is a pokemontcg.io URL; may be
  absent (shouldn't be, as of this writing — see "Current data state").
- `data/guides.json` — piloting-guide HTML per deck, keyed by
  `slug(deckName)` where `slug()` (defined identically in `index.html` and
  in the Python build scripts) lowercases, replaces every run of
  non-alphanumeric characters with `_`, and trims leading/trailing `_`.
- `data/turn1_rules.json` — turn-1 rules (coin flip + what the player
  going first can/can't do) keyed by the exact `year` label used in
  `cards.json` (e.g. `"2010"`, `"2017 NAIC"`). Rendered as an expandable
  box that only appears when a single year is filtered (never on "All
  years"). Hand-maintained, not generated — see `TURN1_RULES.md` for the
  research/sources and the "why" behind each entry. **If you add a new
  year to the collection, add a matching entry here too**, or the box
  just won't show for that year (silent, not an error — `renderTurn1Box()`
  in `index.html` treats a missing key the same as "All years").
- **Matchup Generator tab** — a second top-level tab (`#matchupTab`,
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
slugifying), **except three**, hardcoded in `build_guides.py`'s
`MANUAL_SLUG_OVERRIDES`:

- `Blacephalon_GX_2019.md` (titled "Blacephalon GX (2019)") → deck
  `"Blacephalon (2019)"`
- `Greens_ReshiZard_2019.md` (titled "Green's ReshiZard (2019)") → deck
  `"Green's Reshiram & Charizard (2019)"`
- `Perfection_Mewtwo_2019.md` (titled "Perfection (Mewtwo & Mew-GX)
  (2019)") → deck `"Perfection Mewtwo (2019)"`

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

- 68 decks, 1637 card rows, 15 "formats" (year groupings, including a
  standalone `2017 NAIC`).
- Every row has a `category`. Every row has an `image` — 718 unique image
  URLs, all verified HTTP 200.
- All 68 piloting guides exist and are wired up (`data/guides.json` has 68
  keys, one per deck).
- `data/turn1_rules.json` has an entry for all 15 year labels.

If any of these counts don't match what you find when you pick this
project back up, something changed (Vig added/edited a deck) — that's
expected and fine, just don't assume this doc is still 100% current on
specifics; treat the numbers above as "last known good," and the
*process* described above as the durable part.
