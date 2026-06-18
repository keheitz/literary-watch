## 1. Data pipeline (quote-data)

- [x] 1.1 Vendor the community literary-clock dataset into `tools/data/litclock.csv` (checked in for reproducible offline builds; note: mixed-copyright, used only as a candidate pool — see group 7 for public-domain restriction)
- [x] 1.2 Write `tools/build_quotes.py`: filter to SFW + require title/author, round each time to nearest quarter-hour into 96 slots
- [x] 1.3 In the script, keep the 3 shortest quotes per slot, sorted shortest-first; assert all 96 slots are non-empty
- [x] 1.4 Emit a packed resource blob (96-entry index of offset+count, then `quote\0title\0author\0` records) to `resources/data/quotes.bin`
- [x] 1.5 Register the packed blob as a raw resource in `package.json` and verify it builds under the size target (~70 KB)

## 2. Quote lookup layer (quote-data)

- [x] 2.1 Implement `quotes.c/.h`: load the index, expose `quote_for_slot(slot, date, out_quote, out_title, out_author)` reading only that slot's records from flash
- [x] 2.2 Implement deterministic per-day pick `(day_of_year + slot) % count`
- [x] 2.3 Implement `slot_for_time(h, m)` round-to-nearest-quarter (0..95, wrapping midnight)

## 3. Sky resting state (time-of-day-sky)

- [x] 3.1 Define the 6 time-of-day bands and `band_for_hour(h)`
- [x] 3.2 Create placeholder sky resources for 6 scenes × {kids-color, woodcut-b&w} using per-platform file variants under shared resource IDs
- [x] 3.3 Render the book-page frame + current sky scene; select assets via `PBL_IF_COLOR_ELSE` and layout via `PBL_IF_ROUND_ELSE`
- [x] 3.4 Add the distinct round (chalk) layout
- [x] 3.5 Update the sky scene on each relevant minute tick

## 4. Quote display (quote-display)

- [x] 4.1 Render quote text + title + author inside the book-page frame for both rect and round layouts
- [x] 4.2 Measure the selected quote; draw statically when it fits the page area
- [x] 4.3 Implement slow auto-scroll for overflow; stop and reset scroll on fade-back

## 5. Tap interaction & state machine (tap-reveal)

- [x] 5.1 Define `SKY`/`QUOTE` states and transitions
- [x] 5.2 Subscribe to the accelerometer tap service; tap in `SKY` reveals the current slot's quote
- [x] 5.3 Tap in `QUOTE` re-rolls to another quote in the slot (or holds if single) and restarts the timer
- [x] 5.4 Implement the 20 s auto-fade timer returning to `SKY`

## 6. Integration & polish

- [x] 6.1 Wire `main()` to init window, services, and the state machine; confirm `"watchface": true`
- [x] 6.2 Build all platforms (`pebble build`) and resolve any per-platform resource/RAM issues
- [x] 6.3 Install + screenshot on a color platform (basalt/emery), a b&w platform (diorite), and round (chalk); verify style/layout per platform
- [x] 6.4 Verify flint resolves to the correct style via capability flags (visual check on flint emulator)
- [x] 6.5 Verify tap reveals a quote, re-tap re-rolls, and it fades back after 20 s
- [x] 6.6 Replace placeholder sky art with final kids-color and woodcut illustrations; re-screenshot to confirm
- [ ] 6.7 Round layout polish ("square peg, round hole"): on chalk the rectangular book-page border looks awkward inside the circular screen. Give round displays a circular/round-specific frame (e.g. a ring inset from the bezel) and re-center the sky art and quote text for the circle. (Deferred follow-up; tracked for a future change.)

## 7. Public-domain corpus investigation (quote-data)

- [x] 7.1 Define the public-domain rule of thumb for the project (US: first published ≥ 95 years ago, i.e. ≤ 1930 as of 2026; cross-check author death + 70 years) and record it in `tools/data/README.md`
- [x] 7.2 Assemble an initial set of known public-domain novels from Project Gutenberg (title, author, Gutenberg id) into `tools/data/pd_sources.csv`
- [x] 7.3 Write `tools/pd_mine.py`: download/cache the Gutenberg plain-text editions and search for time expressions (`o'clock`, `half past`, `(a) quarter past/to`, `N minutes past/to`, `noon`/`midnight`, `H:MM`), extracting the containing sentence with book + author and mapping to a quarter-hour slot
- [x] 7.4 Run the initial mining pass and report slot coverage (slots covered, options/slot, empty slots) to gauge how much of the day a PD corpus can cover; expand the source list if coverage is thin
- [x] 7.4a Broaden the source list for authorial balance: curate a wishlist of public-domain women authors and writers of color (`tools/data/pd_wishlist.csv`) and resolve their Gutenberg ids via Gutendex (`tools/resolve_gutenberg_ids.py`), merging into `pd_sources.csv`. Track per-quote author so the final corpus can be balanced where the public domain allows.
- [x] 7.5 Curate mined candidates: verify the stated time maps to the intended slot, trim to a single clean sentence, drop non-SFW
- [x] 7.6 Assemble the public-domain dataset `tools/data/quotes_pd.csv`; decide and document the gap strategy for any still-empty slots (PD-preferred with sky fallback, per the spec)
- [x] 7.7 Point `build_quotes.py` at the PD dataset, regenerate `quotes.bin`, and re-verify coverage + on-watch size
