#!/usr/bin/env python3
"""Build the packed quote resource for the literary-watch watchface.

Reads the vendored public-domain literary-clock dataset and emits a packed
binary blob consumed on-watch by quotes.c.

Pipeline (see openspec design.md):
  1. Filter to SFW entries that have a quote, title, and author.
  2. Round each stated time to the nearest quarter-hour -> one of 96 slots.
  3. Keep the 3 shortest quotes per slot, sorted shortest-first.
  4. Emit: 96-entry index (u16 offset, u8 count) then NUL-delimited records
     (quote \0 title \0 author \0). Offsets are relative to the records
     section. All multi-byte values little-endian.

Run from the project root:  python3 tools/build_quotes.py
"""

import csv
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Input dataset (pipe-delimited). Defaults to the curated public-domain corpus;
# override with a path argument, e.g. `python3 tools/build_quotes.py other.csv`.
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tools" / "data" / "quotes_pd.csv"
OUT = ROOT / "resources" / "data" / "quotes.bin"

NUM_SLOTS = 96
KEEP_PER_SLOT = 3
SIZE_TARGET_BYTES = 70 * 1024  # ~70 KB soft target from design.md

# Title/rank abbreviations whose trailing period is not a real sentence end
# (mirrors tools/pd_mine.py). A quote ending right after one of these is a
# truncated fragment, not a complete sentence, and should be flagged.
ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "st", "prof", "rev", "jr", "sr",
    "mt", "capt", "col", "gen", "lt", "sgt",
}
TRUNCATED_ABBREV = re.compile(
    r"\b(" + "|".join(ABBREVIATIONS) + r")\.$", re.IGNORECASE
)

# Pebble has no room for fancy typography; keep the corpus to characters the
# bundled fonts render. Map the common "smart" punctuation down to ASCII.
TRANSLATE = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", " ": " ",
}


def clean(text):
    text = text.replace("<br/>", "\n")
    for bad, good in TRANSLATE.items():
        text = text.replace(bad, good)
    return text.strip()


def slot_for_time(h, m):
    """Round to nearest quarter-hour, wrapping past midnight -> slot 0..95."""
    q = round((h * 60 + m) / 15) % NUM_SLOTS
    return q


def load_rows():
    slots = [[] for _ in range(NUM_SLOTS)]
    with SRC.open(encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("|")
            if len(parts) < 6:
                continue
            time_str, _quote_time, quote, title, author, sfw = parts[:6]
            if sfw.strip().lower() != "sfw":
                continue
            quote, title, author = clean(quote), clean(title), clean(author)
            if not (quote and title and author):
                continue
            try:
                h, m = int(time_str[:2]), int(time_str[3:5])
            except ValueError:
                continue
            slots[slot_for_time(h, m)].append((quote, title, author))
    return slots


def select(slots):
    """Keep the KEEP_PER_SLOT shortest quotes per slot, shortest-first."""
    out = []
    for entries in slots:
        entries.sort(key=lambda e: len(e[0]))
        out.append(entries[:KEEP_PER_SLOT])
    return out


def pack(selected):
    records = bytearray()
    index = bytearray()
    for entries in selected:
        offset = len(records)
        if offset > 0xFFFF:
            sys.exit("ERROR: records section exceeds u16 offset range")
        index += struct.pack("<HB", offset, len(entries))
        for quote, title, author in entries:
            for field in (quote, title, author):
                records += field.encode("utf-8") + b"\x00"
    return bytes(index) + bytes(records)


def main():
    if not SRC.exists():
        sys.exit(f"ERROR: dataset not found at {SRC}")
    slots = load_rows()

    # Empty slots are allowed (PD-preferred with sky fallback): the watch shows
    # the ambient sky for any quarter-hour with no quote.
    empty = [i for i, s in enumerate(slots) if not s]
    if empty:
        labels = ", ".join(f"{i//4:02d}:{(i%4)*15:02d}" for i in empty)
        print(f"note: {len(empty)} slot(s) have no quote (sky fallback): {labels}")

    selected = select(slots)

    truncated = [
        (quote, title, author)
        for entries in selected
        for quote, title, author in entries
        if TRUNCATED_ABBREV.search(quote)
    ]
    if truncated:
        print(f"WARNING: {len(truncated)} quote(s) look truncated right after "
              "an abbreviation (e.g. \"Mr.\"/\"Mrs.\") -- likely a mining bug, "
              "not a real sentence end:")
        for quote, title, author in truncated:
            print(f'  "{quote}" -- {author}, {title}')

    blob = pack(selected)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(blob)

    total = sum(len(s) for s in selected)
    covered = sum(1 for s in selected if s)
    print(f"slots covered : {covered}/{NUM_SLOTS}")
    print(f"quotes packed : {total}")
    print(f"blob size     : {len(blob)} bytes ({len(blob)/1024:.1f} KB)")
    if len(blob) > SIZE_TARGET_BYTES:
        print(f"WARNING: blob exceeds ~{SIZE_TARGET_BYTES//1024} KB target")
    print(f"written to    : {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
