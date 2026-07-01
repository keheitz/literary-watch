## Why

Many quotes in the shipped corpus cut off mid-sentence right after a title
abbreviation such as "Mr." or "Mrs." (e.g. `"...where Job and Mrs."`). The
root cause is `tools/pd_mine.py`'s sentence splitter, which treats any
`. `/`! `/`? ` as a sentence boundary with no awareness of abbreviations, so
it stops at the first period it finds even when that period belongs to
"Mr.", "Mrs.", "Ms.", "Dr.", "St.", etc. rather than the end of the sentence.
The full Gutenberg source texts are already cached locally
(`tools/data/gutenberg_cache/`, re-fetchable on demand), so this is
repairable by fixing the miner and regenerating the corpus rather than by
filtering the affected entries out.

## What Changes

- Fix `pd_mine.py`'s sentence-boundary detection to not split on periods
  that belong to a common abbreviation (Mr., Mrs., Ms., Dr., St., Prof.,
  Rev., Jr., Sr., etc.), so mined sentences continue to the real sentence
  end.
- Re-run the existing pipeline (`pd_mine.py` -> `curate_pd.py` ->
  `build_quotes.py`) to regenerate `tools/data/pd_candidates.csv`,
  `tools/data/quotes_pd.csv`, and `resources/data/quotes.bin` with complete
  sentences.
- Add a corpus-build check that fails (or reports) if any retained quote's
  text still ends immediately after a known abbreviation, as a regression
  guard against this class of truncation reappearing.

## Capabilities

### Modified Capabilities
- `quote-data`: quotes mined from source texts must end at a true sentence
  boundary, not at a period embedded in a title abbreviation.

## Impact

- `tools/pd_mine.py` (sentence-splitting regex/logic)
- `tools/data/pd_candidates.csv`, `tools/data/quotes_pd.csv` (regenerated)
- `resources/data/quotes.bin` (regenerated, packed corpus shipped on-watch)
- No changes to on-watch C code (`src/c/quotes.c` and friends) — the fix is
  entirely in the offline corpus-build pipeline.
