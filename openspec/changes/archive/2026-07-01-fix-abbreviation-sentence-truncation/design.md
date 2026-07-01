## Context

`tools/pd_mine.py` extracts candidate quotes by finding a clock-time mention
in a Gutenberg source text and expanding outward to the surrounding
sentence via:

```python
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
```

This splits on *any* `.`/`!`/`?` followed by whitespace, including the
period after a title abbreviation ("Mr.", "Mrs.", "Ms.", "Dr.", "St.",
etc.). When the clock-time mention happens to sit right after such an
abbreviation, `sentence_around()` returns a fragment ending at the
abbreviation instead of the real sentence end, e.g.:

```
"Bridgenorth at two o'clock; where Job and Mrs."
```

The affected texts are already cached under `tools/data/gutenberg_cache/`
(gitignored, re-fetched on demand by `fetch()`), so the fix can be applied
by re-running the existing pipeline rather than sourcing new data.

## Goals / Non-Goals

**Goals:**
- Stop treating abbreviation periods as sentence boundaries when mining
  candidate sentences in `pd_mine.py`.
- Regenerate `pd_candidates.csv` -> `quotes_pd.csv` -> `quotes.bin` so the
  shipped corpus no longer contains abbreviation-truncated quotes.
- Add a lightweight guard so this class of truncation is caught by the
  build rather than shipped silently again.

**Non-Goals:**
- Rewriting `curate_pd.py`'s selection/curation logic (weights, SFW filter,
  distribution) — untouched by this change.
- Handling every conceivable abbreviation. A practical, common list (Mr.,
  Mrs., Ms., Dr., St., Prof., Rev., Jr., Sr., Mt., Capt., Col., Gen., Lt.,
  Sgt., etc.) is sufficient; perfect NLP sentence segmentation is out of
  scope for a hobby-project build script.
- Changing on-watch C code — this is purely an offline corpus-build fix.

## Decisions

- **Abbreviation-aware split via negative lookbehind, not a full NLP
  library.** Extend `SENT_SPLIT` (or replace it with a small function) to
  skip a split point when the token immediately before the period matches
  a known abbreviation list. Rationale: the project has zero non-stdlib
  dependencies (`pd_mine.py` docstring: "Pure standard library"); pulling
  in `nltk`/`spacy` for one regex fix is disproportionate.
- **Fix at the mining stage, not the curation or pack stage.** The
  fragment is created when `sentence_around()` first extracts the
  sentence; fixing it there means `pd_candidates.csv` is correct from the
  start and every downstream stage benefits for free.
- **Regenerate the full pipeline output rather than hand-patching
  `quotes_pd.csv`.** Hand-editing the curated CSV would drift from
  `pd_candidates.csv` and be unreproducible. Re-running
  `pd_mine.py -> curate_pd.py -> build_quotes.py` keeps the pipeline as
  the single source of truth.
- **Add a build-time guard in `build_quotes.py`** that flags (prints a
  warning, non-fatal) any retained quote whose text still ends
  immediately after a known abbreviation token. This is a cheap
  regression check independent of the mining fix, since curation could in
  principle introduce a fresh truncated quote later.

## Risks / Trade-offs

- [Abbreviation list is incomplete, some truncations slip through] →
  Mitigate with the build-time guard (flags remaining cases for manual
  review) rather than requiring an exhaustive list up front.
- [Re-mining shifts which sentences are selected as "shortest 3" for a
  slot, since some previously-shortest fragments are now longer complete
  sentences] → Expected and acceptable; re-run `curate_pd.py` and
  `build_quotes.py` fully so the shipped corpus is internally consistent,
  and check the "slots covered" and blob-size output for regressions
  (target: still ≥93/96 slots, ≤~70 KB).
- [Gutenberg source texts not present locally] → `pd_mine.py.fetch()`
  already re-downloads on demand; no new capability needed, just re-run
  time.

## Open Questions

- None blocking; abbreviation list can be extended later if the
  build-time guard surfaces more cases.
