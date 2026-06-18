#!/usr/bin/env python3
"""Curate mined public-domain candidates into a packer-ready dataset.

Reads tools/data/pd_candidates.csv (from pd_mine.py) and produces
tools/data/quotes_pd.csv:  HH:MM|quote_time|quote|title|author|sfw  (24-hour).

Steps (tasks 7.5-7.6):
  - clean sentence fragments, drop slurs (nothing unsafe reaches the watch),
  - resolve AM/PM from sentence context to map each 12-hour quarter onto the
    24-hour clock (ambiguous quotes serve BOTH the AM and PM slot),
  - select up to 3 quotes per slot with a DISTRIBUTION approach:
      * authors are unique within a slot,
      * short quotes are favored,
      * women authors and writers of color are boosted, and
      * heavily-used authors are penalised so authorship spreads across the
        corpus instead of piling onto a few prolific writers.

Author categories come from tools/data/author_tags.csv (author,woman,poc).

Pure standard library. Run from the project root after pd_mine.py.
"""

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "data" / "pd_candidates.csv"
TAGS = ROOT / "tools" / "data" / "author_tags.csv"
OUT = ROOT / "tools" / "data" / "quotes_pd.csv"

KEEP_PER_SLOT = 3
# Selection weights (lower score = picked first). Tune these to trade quote
# length against representation/distribution.
W_WOMAN = 45        # score bonus for a woman author
W_POC = 45          # score bonus for a writer of color (stacks -> WOC = -90)
USAGE_PENALTY = 15  # added per prior selection of the same author

SLURS = re.compile(
    r"\b(nigger|niggers|nigga|darkie|darky|darkies|coon|chink|chinaman|"
    r"kike|wop|dago|redskin|redskins|squaw|half-breed)\b",
    re.IGNORECASE,
)

PM_HINTS = ("afternoon", "evening", "night", "tonight", "p.m", "p. m",
            "dinner", "supper", "dusk", "sunset")
AM_HINTS = ("morning", "a.m", "a. m", "dawn", "daybreak", "sunrise",
            "breakfast", "forenoon")


def load_tags():
    tags = {}
    if TAGS.exists():
        for r in csv.DictReader(TAGS.open()):
            tags[r["author"]] = (r["woman"].strip() == "1", r["poc"].strip() == "1")
    return tags


def clean(sentence):
    s = re.sub(r'^[\s"“”‘’.,;:!?)\-—]+', "", sentence.strip())
    return re.sub(r"\s+", " ", s).strip()


def am_pm_targets(h12, qm, kind, sentence):
    low = sentence.lower()
    if kind == "noon":
        return [(12, qm)]
    if kind == "midnight":
        return [(0, qm)]
    if h12 == 12:
        return [(0, qm), (12, qm)]
    has_pm = any(h in low for h in PM_HINTS)
    has_am = any(h in low for h in AM_HINTS)
    if has_am and not has_pm:
        return [(h12, qm)]
    if has_pm and not has_am:
        return [(h12 + 12, qm)]
    return [(h12, qm), (h12 + 12, qm)]


def main():
    tags = load_tags()
    missing = set()

    def category_bonus(author):
        woman, poc = tags.get(author, (False, False))
        if author not in tags:
            missing.add(author)
        return (-W_WOMAN if woman else 0) + (-W_POC if poc else 0)

    # Gather candidates per 24h slot (deduped by quote text).
    by_slot = defaultdict(list)   # (hh,mm) -> [(quote,title,author)]
    seen = set()
    dropped_slur = 0
    for r in csv.DictReader(SRC.open()):
        quote = clean(r["sentence"])
        if SLURS.search(quote):
            dropped_slur += 1
            continue
        if not (40 <= len(quote) <= 220):
            continue
        h12, qm = int(r["slot12"][:2]), int(r["slot12"][3:5])
        for hh, mm in am_pm_targets(h12, qm, r["kind"], r["sentence"]):
            key = (hh, mm, quote)
            if key not in seen:
                seen.add(key)
                by_slot[(hh, mm)].append((quote, title_of(r), r["author"]))

    # Distribution selection: multi-pass so every slot gets its first quote
    # before any slot gets a third.
    usage = Counter()
    chosen = defaultdict(list)
    slots = sorted(by_slot)
    for _pass in range(KEEP_PER_SLOT):
        for slot in slots:
            if len(chosen[slot]) > _pass:
                continue
            picked_authors = {a for _, _, a in chosen[slot]}
            pool = [c for c in by_slot[slot] if c[2] not in picked_authors
                    and c not in chosen[slot]]
            if not pool:
                continue
            best = min(pool, key=lambda c: len(c[0]) + category_bonus(c[2])
                       + USAGE_PENALTY * usage[c[2]])
            chosen[slot].append(best)
            usage[best[2]] += 1

    out_rows = []
    for slot in slots:
        for quote, title, author in sorted(chosen[slot], key=lambda c: len(c[0])):
            out_rows.append((slot[0], slot[1], quote, title, author))

    with OUT.open("w", newline="") as f:
        w = csv.writer(f, delimiter="|")
        for hh, mm, quote, title, author in out_rows:
            w.writerow([f"{hh:02d}:{mm:02d}", f"{hh:02d}:{mm:02d}", quote, title, author, "sfw"])

    # Report.
    n = len(out_rows)
    women = sum(1 for *_, a in out_rows if tags.get(a, (0, 0))[0])
    poc = sum(1 for *_, a in out_rows if tags.get(a, (0, 0))[1])
    covered = {(hh, mm) for hh, mm, *_ in out_rows}
    all96 = {(h, q) for h in range(24) for q in (0, 15, 30, 45)}
    empty = sorted(all96 - covered)
    print(f"rows written     : {n}  -> {OUT.relative_to(ROOT)}")
    print(f"dropped (slurs)  : {dropped_slur}")
    print(f"women authors    : {women} ({100*women/n:.0f}%)")
    print(f"writers of color : {poc} ({100*poc/n:.0f}%)")
    print(f"distinct authors : {len(set(a for *_, a in out_rows))}")
    top = Counter(a for *_, a in out_rows).most_common(6)
    print("most-used authors: " + ", ".join(f"{a.split()[-1]}({c})" for a, c in top))
    print(f"24h slots covered: {len(covered)}/96  (empty: "
          + (", ".join(f'{h:02d}:{m:02d}' for h, m in empty) or "none") + ")")
    if missing:
        print(f"\n  WARNING: {len(missing)} author(s) not in author_tags.csv: "
              + ", ".join(sorted(missing)))


def title_of(row):
    return row["title"]


if __name__ == "__main__":
    main()
