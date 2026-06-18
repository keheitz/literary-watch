# Quote corpus — data & provenance

The watchface tells time with short literary quotes that name the current
quarter-hour. The shipped corpus (`resources/data/quotes.bin`) is built only
from **public-domain** works.

## Public-domain rule of thumb

A source is treated as public domain for this project if **either** holds:

- **US publication rule** — first published at least **95 years ago**. As of
  2026 that means **first published in or before 1930**. (US copyright restored
  to a rolling 95-year term; the cutoff advances by one year each January.)
- **Life + 70 rule** — the author died at least **70 years ago** (covers most
  of the EU/UK and other "life + 70" jurisdictions).

When the two disagree, prefer the **more conservative** answer (i.e. only treat
as public domain if it is clearly out of copyright). Borderline 1920s titles
(e.g. *The Great Gatsby*, 1925; *Mrs. Spring Fragrance*, 1912) are included
because they satisfy the US publication rule as of 2026.

This is a practical heuristic, not legal advice. Jurisdictions differ; if the
watchface is ever **distributed or sold**, re-verify each source for the target
markets (translations in particular can carry a separate translator copyright).

## Sources

`pd_sources.csv` — the public-domain novels mined for quotes, one row per work
(`gutenberg_id,title,author`). Full texts come from **Project Gutenberg**
(`https://www.gutenberg.org/cache/epub/<id>/pg<id>.txt`) and are cached under
`gutenberg_cache/` (gitignored; re-downloaded on demand).

`pd_wishlist.csv` — a curated `author,title` list used to broaden the roster
toward women authors and writers of color. `resolve_gutenberg_ids.py` looks up
their Gutenberg ids via the Gutendex API and merges them into `pd_sources.csv`.

## Build pipeline

```
pd_wishlist.csv ──resolve_gutenberg_ids.py──▶ pd_sources.csv
pd_sources.csv  ──pd_mine.py──▶ pd_candidates.csv   (mine time-naming sentences)
pd_candidates.csv ──curate_pd.py──▶ quotes_pd.csv   (clean, slur-filter, AM/PM → 24h,
                                                     distribution selection ≤3/slot)
quotes_pd.csv   ──build_quotes.py──▶ resources/data/quotes.bin  (pack)
```

Regenerate from scratch:

```bash
python3 tools/resolve_gutenberg_ids.py   # optional: refresh ids from the wishlist
python3 tools/pd_mine.py                 # mine candidates (downloads on first run)
python3 tools/curate_pd.py               # -> tools/data/quotes_pd.csv
python3 tools/build_quotes.py            # -> resources/data/quotes.bin
```

## Notes

- **SFW** — `curate_pd.py` drops any candidate containing a slur so nothing
  unsafe reaches the watch (several period works use such language).
- **Coverage / gaps** — the corpus covers 93 of the 96 quarter-hour slots; the
  remaining slots fall back to the ambient sky view (no quote shown).
- **Selection / distribution** — `curate_pd.py` chooses up to 3 quotes per slot
  with authors unique within a slot, favoring short quotes while boosting women
  authors and writers of color and penalising over-used authors so authorship
  spreads across the corpus. Categories come from `author_tags.csv`; tune the
  `W_WOMAN`, `W_POC`, and `USAGE_PENALTY` weights at the top of `curate_pd.py`.
  Current corpus: ~52% women authors, ~21% writers of color, across 61 authors
  (vs. 27% / 3% under a plain shortest-quote rule).
- `litclock.csv` is a separate, **mixed-copyright** community dataset kept only
  as a reference candidate pool. It is **not** used to build the shipped corpus.
