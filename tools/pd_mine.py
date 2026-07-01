#!/usr/bin/env python3
"""Mine public-domain Project Gutenberg texts for time-of-day quotes.

Initial-search tool for the public-domain corpus investigation (tasks 7.2-7.4).
Downloads (and caches) the plain-text editions listed in pd_sources.csv, finds
sentences that name a clock time, maps each to a quarter-hour, and reports how
much of the day a public-domain corpus can cover.

Spelled-out times are 12-hour and AM/PM-ambiguous, so coverage is reported over
the 48 twelve-hour quarter positions (hour 1-12 x :00/:15/:30/:45); AM/PM is a
curation choice made later. noon/midnight are reported separately.

Pure standard library. Run from the project root: python3 tools/pd_mine.py
"""

import csv
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "tools" / "data" / "pd_sources.csv"
CACHE = ROOT / "tools" / "data" / "gutenberg_cache"
OUT = ROOT / "tools" / "data" / "pd_candidates.csv"

NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}
NUMWORD = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"


def fetch(gid):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"pg{gid}.txt"
    if path.exists() and path.stat().st_size > 1000:
        return path.read_text(encoding="utf-8", errors="ignore")
    url = f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
    req = urllib.request.Request(url, headers={"User-Agent": "literary-watch-research/1.0"})
    try:
        data = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    except Exception as e:  # noqa: BLE001
        print(f"  ! failed {gid}: {e}", file=sys.stderr)
        return None
    path.write_text(data, encoding="utf-8")
    return data


def quarter(minute):
    return (round(minute / 15) * 15) % 60, (1 if round(minute / 15) == 4 else 0)


def parse_time(m):
    """Return (hour12, quarter_minute, kind) for a regex match dict, or None.
    hour12 in 1..12; quarter_minute in {0,15,30,45}; kind labels the pattern."""
    g = m.groupdict()
    if g.get("noon"):
        return (12, 0, "noon")
    if g.get("midnight"):
        return (12, 0, "midnight")  # tracked separately by caller via kind
    if g.get("hh"):
        h = int(g["hh"]); mm = int(g["mm"])
        if h == 0 or h > 23 or mm > 59:
            return None
        qm, carry = quarter(mm)
        h12 = ((h + carry - 1) % 12) + 1
        return (h12, qm, "numeric")
    base = g.get("oc") or g.get("hp") or g.get("qp") or g.get("qt") or g.get("mp") or g.get("mt")
    if not base:
        return None
    hour = NUM[base.lower()]
    if g.get("oc"):
        return (hour, 0, "oclock")
    if g.get("hp"):
        return (hour, 30, "half_past")
    if g.get("qp"):
        return (hour, 15, "quarter_past")
    if g.get("qt"):
        h12 = ((hour - 2) % 12) + 1
        return (h12, 45, "quarter_to")
    if g.get("mp"):
        qm, carry = quarter(NUM[g["mpmin"].lower()])
        h12 = ((hour + carry - 1) % 12) + 1
        return (h12, qm, "minutes_past")
    if g.get("mt"):
        mins = NUM[g["mtmin"].lower()]
        qm, carry = quarter(60 - mins)
        h12 = ((hour - 2 + carry) % 12) + 1
        return (h12, qm, "minutes_to")
    return None


PATTERN = re.compile(
    r"\b(?P<hh>\d{1,2}):(?P<mm>\d{2})\b"
    rf"|\b(?P<oc>{NUMWORD})\s+o.?clock\b"
    rf"|\bhalf[-\s]past\s+(?P<hp>{NUMWORD})\b"
    rf"|\b(?:a\s+)?quarter[-\s]past\s+(?P<qp>{NUMWORD})\b"
    rf"|\b(?:a\s+)?quarter\s+(?:to|before)\s+(?P<qt>{NUMWORD})\b"
    rf"|\b(?P<mpmin>{NUMWORD})\s+minutes?\s+past\s+(?P<mp>{NUMWORD})\b"
    rf"|\b(?P<mtmin>{NUMWORD})\s+minutes?\s+to\s+(?P<mt>{NUMWORD})\b"
    r"|\b(?P<noon>noon|midday)\b"
    r"|\b(?P<midnight>midnight)\b",
    re.IGNORECASE,
)

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Title/rank abbreviations whose period is not a sentence end. Checked
# case-insensitively against the word immediately before the punctuation.
ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "st", "prof", "rev", "jr", "sr",
    "mt", "capt", "col", "gen", "lt", "sgt",
}


def split_sentences(text):
    """Like SENT_SPLIT.split(text), but does not split right after a known
    abbreviation (e.g. "Mrs.", "Dr."), since that period isn't a real
    sentence end -- the split is deferred to the next boundary instead."""
    pieces = []
    start = 0
    for m in SENT_SPLIT.finditer(text):
        preceding = text[start:m.start()]
        word = re.search(r"([A-Za-z]+)[.!?]$", preceding)
        if word and word.group(1).lower() in ABBREVIATIONS:
            continue
        pieces.append(preceding)
        start = m.end()
    pieces.append(text[start:])
    return pieces


def sentence_around(text, start, end):
    lo = max(0, start - 300)
    hi = min(len(text), end + 300)
    window = re.sub(r"\s+", " ", text[lo:hi]).strip()
    rel = start - lo
    pieces = split_sentences(window)
    pos = 0
    for p in pieces:
        if pos <= rel <= pos + len(p) + 1:
            return p.strip()
        pos += len(p) + 1
    return window


def main():
    rows = list(csv.DictReader(SOURCES.open()))
    # slot key: (hour12, quarter_minute); plus special noon/midnight buckets
    by_slot = defaultdict(list)
    specials = defaultdict(list)
    candidates = []

    for row in rows:
        gid = row["gutenberg_id"]
        text = fetch(gid)
        if not text:
            continue
        found = 0
        for m in PATTERN.finditer(text):
            parsed = parse_time(m)
            if not parsed:
                continue
            h12, qm, kind = parsed
            sent = sentence_around(text, m.start(), m.end())
            if not (40 <= len(sent) <= 240):
                continue
            if kind in ("noon", "midnight"):
                specials[kind].append((sent, row["title"], row["author"]))
            else:
                by_slot[(h12, qm)].append((sent, row["title"], row["author"]))
            candidates.append((f"{h12:02d}:{qm:02d}", kind, sent, row["title"], row["author"]))
            found += 1
        print(f"  {row['title'][:34]:34s} {found:5d} time mentions")

    all_slots = [(h, q) for h in range(1, 13) for q in (0, 15, 30, 45)]
    covered = [s for s in all_slots if by_slot[s]]
    empty = [s for s in all_slots if not by_slot[s]]
    print("\n=== Public-domain coverage (48 twelve-hour quarter slots) ===")
    print(f"  slots covered : {len(covered)}/48")
    print(f"  total candidate sentences: {len(candidates)}")
    print(f"  noon mentions: {len(specials['noon'])}  midnight mentions: {len(specials['midnight'])}")
    print("  empty slots   : " +
          (", ".join(f"{h}:{q:02d}" for h, q in empty) or "none"))

    print("\n  sample quotes:")
    for s in covered[:8]:
        sent, title, author = min(by_slot[s], key=lambda e: len(e[0]))
        print(f"   [{s[0]}:{s[1]:02d}] \"{sent}\" -- {author}, {title}")

    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["slot12", "kind", "sentence", "title", "author"])
        w.writerows(candidates)
    print(f"\n  wrote {len(candidates)} candidates to {OUT.relative_to(ROOT)}")


def _selftest():
    """Smoke test for split_sentences(): confirms abbreviation periods
    (e.g. "Mrs.") are not treated as sentence boundaries. Run with
    `python3 tools/pd_mine.py --selftest`."""
    text = (
        "But a visitor had come in at one o'clock, and Mr. Bridgenorth at "
        "two o'clock; where Job and Mrs. Watson waited. She left at three."
    )
    pieces = split_sentences(text)
    assert not any(p.strip().endswith(("Mr.", "Mrs.")) for p in pieces), pieces
    assert any("Watson waited." in p for p in pieces), pieces
    print("pd_mine self-test passed:", pieces)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        main()
