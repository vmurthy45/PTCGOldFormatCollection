# Pokémon TCG turn-1 rules, 2004–present

Research notes for the "Turn 1 Rules" box shown on the site when a single
year is filtered. This file is the human-readable source; the site
actually reads the condensed `data/turn1_rules.json` (see the bottom of
this file for how the two relate).

## Why this exists

The rule for what the player going first is and isn't allowed to do on
their first turn has changed multiple times across the game's history —
it's not a constant. Three things have moved independently over time:

1. **Does the player going first draw a card** on their first turn?
2. **Can the player going first play Supporter cards** (and, in some
   eras, Items/Stadiums too) on their first turn?
3. **Can the player going first attack** on their first turn?

A fourth thing changed once and stayed changed: whether the winner of the
opening coin flip **must** go first, or **gets to choose**.

## The timeline

| Era | Draw | Supporters / Items / Stadium | Attack |
|---|---|---|---|
| WotC era (1999 – ~2003) | Normal | All allowed | Allowed |
| 2004 Worlds – 2006 | **Skipped** | **Not allowed** | Allowed |
| 2007 – 2010 (Diamond & Pearl / HeartGold & SoulSilver era) | Normal (must draw) | **Not allowed** | Allowed |
| 2011 – 2013 (Black & White era) | Normal | All allowed | Allowed |
| 2014 – Feb 20, 2020 (XY through early Sun & Moon/pre-Sword & Shield) | Normal | All allowed | **Not allowed** |
| Feb 21, 2020 – present (Sword & Shield through Scarlet & Violet) | Normal | Items & Stadium allowed; **Supporters not allowed** | **Not allowed** |

Key turning points:

- **2004 Worlds**: the player going first stops drawing a card on turn 1,
  and loses the ability to play Supporter/Trainer/Stadium cards. This
  lasts through the Diamond & Pearl era.
- **Black & White (Feb 2011)**: the game fully reverts to "no first-turn
  restrictions at all" — draw normally, play anything, attack if you can.
  This is the only era in the game's history (other than the earliest
  WotC years) with genuinely zero first-turn restrictions.
- **XY (Feb 2014)**: for the first time, the game restricts *attacking* on
  turn 1 for the player going first — this is the "donk" problem (turn-1
  knockouts off cards like Sableye SF/Machamp SF) finally getting
  addressed directly, rather than by choking off Supporters. Trainer
  cards (Supporters included) become fully unrestricted again.
- **Kalos Starter Set (also ~Feb 2014, same window as XY)**: the *coin
  flip itself* changes. Before this, the flip happened after both players
  set up their hand/prizes, and the winner was **forced** to go first.
  From this point on, the flip happens before either player draws an
  opening hand, and the **winner chooses** who goes first.
- **Sword & Shield (Feb 21, 2020)**: Supporters get banned on turn 1
  again — but this time *only* Supporters. Items and Stadiums stay legal.
  This is layered on top of the still-active "no attack" rule from 2014,
  giving the modern two-part restriction. Confirmed current via the
  official rulebook PDF (see Sources) and via a February 2026 rulebook
  update that touched other mechanics but left this rule untouched.

Two things that are **not** part of this comparison because they haven't
meaningfully changed across any year this site covers: attaching Energy
from hand has never been restricted on turn 1 for either player, and
"can't evolve a Pokémon on the turn it was played or on either player's
first turn" is a separate, evergreen rule that applies to *both* players
equally (not specific to the player going first), so it doesn't belong on
a "player going first" checklist.

## Mapped to this site's years

The site's `year` field is the Worlds year the deck was played in (i.e.
"which ruleset was live around August of that year"), not a calendar-year
rules snapshot. Mapping the timeline above onto that:

| Site year(s) | Ruleset in effect | Flip |
|---|---|---|
| 2010 | 2007–2010 (Diamond & Pearl / HGSS era) | Winner must go first |
| 2012, 2013 | 2011–2013 (Black & White era) | Winner must go first |
| 2014, 2015, 2016, 2017, 2017 NAIC, 2018, 2019 | XY – pre-Sword & Shield | Winner chooses |
| 2020, 2022, 2023, 2024, 2025 | Sword & Shield onward | Winner chooses |

(2011 and 2021 have no decklists in this collection, so they don't need
an entry — see `piloting_guides_collection/README.md`.)

## Display format used on the site

Each card-type/action is stored as its own atomic entry in
`data/turn1_rules.json` (`{label, allowed}`), and `index.html` groups them
by `allowed` at render time — one ✅ line and one ❌ line, each a
`/`-joined list of every label sharing that status. So the underlying
data for 2020 is four separate entries (Items, Stadium, Supporters,
Attack), but it renders as exactly two lines:

**2010**
```
Flip: Winner Goes First
Player going first:
✅ Attack
❌ Supporters/Items/Stadium
```

**2012, 2013**
```
Flip: Winner Goes First
Player going first:
✅ Items/Supporters/Stadium/Attack
```

**2014 – 2019 (incl. 2017 NAIC)**
```
Flip: Winner Chooses
Player going first:
✅ Items/Supporters/Stadium
❌ Attack
```

**2020, 2022 – 2025**
```
Flip: Winner Chooses
Player going first:
✅ Items/Stadium
❌ Supporters/Attack
```

## Sources

- [Official Pokémon TCG rulebook PDF](https://www.pokemon.com/static-assets/content-assets/cms2/pdf/trading-card-game/rulebook/par_rulebook_en.pdf) —
  primary source for the current rule text: *"The player who goes first
  cannot play a Supporter card on their first turn"* and *"On the first
  turn of the game, the starting player skips [the Attack] step."* Also
  confirms the modern coin-flip rule: *"Flip a coin. The winner of the
  coin flip decides which player goes first."*
- [What Were the "First Turn" Rules Throughout the Years? — PokéBeach forums](https://www.pokebeach.com/forums/threads/what-were-the-first-turn-rules-throughout-the-years.132645/) —
  community-compiled era-by-era breakdown, cross-checked against the
  other sources below.
- [First Turn Rules – Full — Pokémon TCG Archive](https://ptcgarchive.com/first-turn-rules-full/) —
  year-by-year table for WotC era through 2013 (Black & White); this
  site's numbers for 2004–2013 are taken from here.
- [Pokémon Trading Card Game Rules Recap for Returning Players — TCGplayer](https://www.tcgplayer.com/content/article/Pok%C3%A9mon-Trading-Card-Game-Rules-Recap-for-Returning-Players/920ea10a-85e2-4f13-8f6f-b98d88ba0031/) —
  corroborates the XY-era attack restriction and the WotC-era baseline.
- [New Turn 1 Supporter Rule Change — Card Cavern Trading Cards](https://www.cardcaverntradingcards.com/blogs/news/new-turn-1-supporter-rule-change-what-you-need-to-know) —
  the February 21, 2020 Sword & Shield Supporter-ban announcement, with
  the exact effective date.
- [Coin (TCG) — Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Coin_(TCG)) —
  the coin-flip mechanic change from "winner forced to go first" to
  "winner chooses," tied to the Kalos Starter Set (XY's release window,
  Feb 2014).
- [February 2026 TCG rulebook updates — The PokeGym](https://pokegym.net/2026/02/21/february-2026-tcg-rulebook-updates/) —
  used to confirm the Supporter/attack turn-1 rules were **not** touched
  by the most recent rulebook revision, i.e. still current as of this
  writing.

## Relationship to `data/turn1_rules.json`

`data/turn1_rules.json` is a hand-maintained, condensed version of the
"Mapped to this site's years" table above — one entry per site `year`
label, each with a `flip` string and a `rules` array of
`{label, allowed}` pairs, in the exact order they should render. If a new
year is ever added to the collection whose Worlds format isn't already
covered by one of the four buckets above (e.g. a future rule change),
add a new row to this file's tables first, then add the corresponding
entry to the JSON — don't just add to the JSON without updating this
research doc, or the two will drift apart.
