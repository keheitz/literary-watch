#!/usr/bin/env python3
"""Generate placeholder sky illustrations for the 6 time-of-day scenes.

These are stand-ins so the resource pipeline and per-platform selection can be
validated now; final kids-color and woodcut art replaces them later (task 6.6).

For each scene we emit two tagged variants under a shared resource id:
  resources/images/sky/<scene>~color.png   (vertical gradient, all color platforms)
  resources/images/sky/<scene>~bw.png      (grayscale gradient, all b&w platforms)

Pure standard library (zlib) — no Pillow required.
"""

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "resources" / "images" / "sky"

# Color variants sized to cover the largest color screen (emery 200x228);
# b&w variants sized for the b&w screens (aplite/diorite 144x168).
COLOR_W, COLOR_H = 200, 228
BW_W, BW_H = 144, 168

# scene -> (top RGB, bottom RGB) vertical gradient
SCENES = {
    "dawn":      ((255, 180, 120), (120, 160, 220)),
    "morning":   ((150, 200, 255), (220, 240, 255)),
    "midday":    (( 90, 160, 235), (180, 220, 255)),
    "afternoon": ((120, 180, 235), (240, 220, 170)),
    "dusk":      ((255, 140,  90), ( 60,  50, 110)),
    "night":     (( 10,  12,  40), ( 40,  30,  70)),
}


def write_png(path, width, height, rgb_rows):
    """Write an 8-bit truecolor PNG from a list of rows of (r,g,b) tuples."""
    raw = bytearray()
    for row in rgb_rows:
        raw.append(0)  # filter type 0 (None) for this scanline
        for r, g, b in row:
            raw += bytes((r, g, b))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    path.write_bytes(png)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient_rows(width, height, top, bottom, grayscale=False):
    rows = []
    for y in range(height):
        t = y / max(height - 1, 1)
        c = lerp(top, bottom, t)
        if grayscale:
            g = round(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
            c = (g, g, g)
        rows.append([c] * width)
    return rows


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for scene, (top, bottom) in SCENES.items():
        write_png(OUT_DIR / f"{scene}~color.png", COLOR_W, COLOR_H,
                  gradient_rows(COLOR_W, COLOR_H, top, bottom))
        write_png(OUT_DIR / f"{scene}~bw.png", BW_W, BW_H,
                  gradient_rows(BW_W, BW_H, top, bottom, grayscale=True))
        print(f"wrote {scene}~color.png and {scene}~bw.png")
    print(f"-> {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
