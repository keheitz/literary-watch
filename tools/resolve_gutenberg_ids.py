#!/usr/bin/env python3
"""Resolve Gutenberg ids for a wishlist of authors/titles via the Gutendex API.

Reads tools/data/pd_wishlist.csv (author,title), queries https://gutendex.com
for each, picks the best matching public-domain text, and merges the resolved
(gutenberg_id,title,author) rows into tools/data/pd_sources.csv (deduped by id).

Used to broaden the corpus toward authorial balance (task 7.4a) without
hand-guessing ids. Unresolved entries are reported so they can be fixed by hand.

Pure standard library. Run from the project root.
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WISHLIST = ROOT / "tools" / "data" / "pd_wishlist.csv"
SOURCES = ROOT / "tools" / "data" / "pd_sources.csv"


def surname(author):
    return author.replace(".", "").split()[-1].lower()


def gutendex(query):
    url = "https://gutendex.com/books?search=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": "literary-watch-research/1.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
    return data.get("results", [])


def best_match(results, want_author):
    sn = surname(want_author)
    for r in results:
        # English plain-text edition by the right author wins.
        authors = " ".join(a["name"].lower() for a in r.get("authors", []))
        if sn in authors and "en" in r.get("languages", ["en"]):
            return r
    return results[0] if results else None


def main():
    existing = {}
    if SOURCES.exists():
        for row in csv.DictReader(SOURCES.open()):
            existing[row["gutenberg_id"]] = row

    added, unresolved = [], []
    for row in csv.DictReader(WISHLIST.open()):
        author, title = row["author"], row["title"]
        try:
            results = gutendex(f"{title} {author}")
            match = best_match(results, author)
        except Exception as e:  # noqa: BLE001
            print(f"  ! query failed: {title} — {e}", file=sys.stderr)
            unresolved.append((author, title))
            continue
        if not match:
            unresolved.append((author, title))
            print(f"  ? no match: {author} — {title}")
            continue
        gid = str(match["id"])
        if gid not in existing:
            existing[gid] = {"gutenberg_id": gid, "title": title, "author": author}
            added.append((gid, title, author))
            print(f"  + {gid:>6}  {author} — {title}")
        time.sleep(0.3)  # be polite to the API

    # Rewrite sources sorted by id for stable diffs.
    with SOURCES.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["gutenberg_id", "title", "author"])
        w.writeheader()
        for gid in sorted(existing, key=lambda x: int(x)):
            w.writerow(existing[gid])

    print(f"\n  added {len(added)} new sources; {len(existing)} total")
    if unresolved:
        print("  unresolved (fix by hand): " +
              "; ".join(f"{a} — {t}" for a, t in unresolved))


if __name__ == "__main__":
    main()
