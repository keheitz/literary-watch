## 1. Fix sentence-boundary detection in the miner

- [x] 1.1 In `tools/pd_mine.py`, define a list of common title/rank
      abbreviations (Mr., Mrs., Ms., Dr., St., Prof., Rev., Jr., Sr., Mt.,
      Capt., Col., Gen., Lt., Sgt., etc.)
- [x] 1.2 Replace/extend `SENT_SPLIT` so it does not split immediately
      after a period whose preceding token matches a known abbreviation
- [x] 1.3 Add/update a small unit check (or inline `if __name__` smoke
      test) confirming `sentence_around()` no longer stops at
      "...and Mrs." for a synthetic example

## 2. Add a build-time truncation guard

- [x] 2.1 In `tools/build_quotes.py`, add a check that flags any selected
      quote whose text ends immediately after a known abbreviation token
      (reuse the abbreviation list from `pd_mine.py` or a shared
      constant)
- [x] 2.2 Print a clear warning listing any flagged quotes (title/author)
      so they can be reviewed before shipping

## 3. Regenerate the corpus

- [x] 3.1 Run `python3 tools/pd_mine.py` to re-mine candidates with the
      fixed sentence splitter (re-downloads cached Gutenberg texts as
      needed)
- [x] 3.2 Run `python3 tools/curate_pd.py` to re-curate
      `tools/data/quotes_pd.csv`
- [x] 3.3 Spot-check previously-truncated entries (search for quotes
      ending in "Mr." / "Mrs." / "Ms." / "Dr." in the regenerated CSV) and
      confirm none remain
- [x] 3.4 Run `python3 tools/build_quotes.py` and confirm no truncation
      warnings from task 2.1, slot coverage stays ≥93/96, and blob size
      stays within the ~70 KB target

## 4. Verify on-watch

- [x] 4.1 `pebble build` and `pebble install --emulator basalt`
- [x] 4.2 Cycle through several quarter-hour slots via emulator time-set
      and screenshot to confirm previously-truncated quotes now render
      complete sentences
- [x] 4.3 Update `openspec/specs/quote-data/spec.md` via sync once the
      change is archived
