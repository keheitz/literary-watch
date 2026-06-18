#!/usr/bin/env python3
"""Generate stylized time-of-day sky art for the watchface (task 6.6).

Two styles, matching the design:
  * COLOR  (basalt/chalk/emery): flat kids-illustration, every colour snapped to
    the Pebble 64-colour palette (channels in {0,85,170,255}) so what you see is
    what renders.  200x228 to cover the largest colour screen.
  * BW     (aplite/diorite/flint): woodcut / engraving — pure black ink on white
    (night inverts to carved white on black), no greys to dither.  144x168.

Writes resources/images/sky/<scene>~{color,bw}.png for the six scenes.
Pure standard library (zlib). Run from the project root.
"""

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "resources" / "images" / "sky"
CW, CH = 200, 228   # colour canvas
BW, BH = 144, 168   # b&w canvas

# --- Pebble-safe colours (channels snapped to 0/85/170/255) ---
WHITE=(255,255,255); BLACK=(0,0,0); GREY=(170,170,170)
YELLOW=(255,255,0); GOLD=(255,170,0); ORANGE=(255,85,0)
PEACH=(255,170,170); PINK=(255,85,170)
SKY=(85,170,255); BLUE=(0,170,255); DEEPBLUE=(0,85,170); NAVY=(0,0,85)
PURPLE=(85,0,170); PLUM=(170,0,170)
MOON=(255,255,170); GREEN=(0,170,0); DARKGREEN=(0,85,0)


# ---------- tiny raster toolkit ----------
def canvas(w, h, bg):
    return [[list(bg) for _ in range(w)] for _ in range(h)]


def px(img, x, y, c):
    if 0 <= y < len(img) and 0 <= x < len(img[0]):
        img[y][x] = list(c)


def band(img, y0, y1, c):
    for y in range(max(0, y0), min(len(img), y1)):
        for x in range(len(img[0])):
            img[y][x] = list(c)


def disc(img, cx, cy, r, c, half=None):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                if half == "top" and y > cy:
                    continue
                px(img, x, y, c)


def line(img, x0, y0, x1, y1, c, t=1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx - dy
    while True:
        for ox in range(-(t // 2), t - t // 2):
            for oy in range(-(t // 2), t - t // 2):
                px(img, x0 + ox, y0 + oy, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy; x0 += sx
        if e2 < dx:
            err += dx; y0 += sy


def rays(img, cx, cy, r0, r1, n, c, t=1, span=6.283185, start=0.0):
    import math
    for i in range(n):
        a = start + span * i / n
        line(img, int(cx + r0 * math.cos(a)), int(cy + r0 * math.sin(a)),
             int(cx + r1 * math.cos(a)), int(cy + r1 * math.sin(a)), c, t)


def ring(img, cx, cy, r, c, t=2):
    import math
    for d in range(720):
        a = math.radians(d / 2)
        for k in range(t):
            px(img, int(cx + (r + k) * math.cos(a)), int(cy + (r + k) * math.sin(a)), c)


def cloud(img, cx, cy, s, c):
    for dx, dy, rr in [(-s, 0, s), (0, -s // 2, int(s * 1.3)), (s, 0, s),
                       (0, s // 3, int(s * 1.1))]:
        disc(img, cx + dx, cy + dy, rr, c)


def hatch(img, x0, y0, x1, y1, step, c, t=1):
    # diagonal parallel lines (engraving shading)
    for d in range(-(y1 - y0), (x1 - x0), step):
        line(img, x0 + max(0, d), y0 + max(0, -d),
             min(x1, x0 + d + (y1 - y0)), min(y1, y0 + (x1 - x0) - d), c, t)


def stars(img, pts, c):
    for x, y in pts:
        px(img, x, y, c); px(img, x - 1, y, c); px(img, x + 1, y, c)
        px(img, x, y - 1, c); px(img, x, y + 1, c)


# ---------- colour (kids) scenes ----------
def color_scene(name):
    img = canvas(CW, CH, SKY)
    g = CH - 22  # ground line
    if name == "dawn":
        band(img, 0, 70, PEACH); band(img, 70, 140, PINK); band(img, 140, g, SKY)
        disc(img, 100, g, 40, GOLD)            # rising sun on horizon
        cloud(img, 150, 60, 12, WHITE); cloud(img, 45, 95, 9, WHITE)
    elif name == "morning":
        band(img, 0, g, SKY)
        disc(img, 56, 60, 26, YELLOW)
        cloud(img, 130, 80, 13, WHITE); cloud(img, 60, 140, 10, WHITE)
        cloud(img, 165, 140, 11, WHITE)
    elif name == "midday":
        band(img, 0, g, BLUE)
        disc(img, 100, 48, 32, YELLOW)
        cloud(img, 45, 120, 12, WHITE); cloud(img, 150, 150, 13, WHITE)
    elif name == "afternoon":
        band(img, 0, 120, SKY); band(img, 120, g, PEACH)
        disc(img, 150, 120, 28, GOLD)
        cloud(img, 60, 70, 13, WHITE); cloud(img, 110, 150, 11, WHITE)
    elif name == "dusk":
        band(img, 0, 70, ORANGE); band(img, 70, 135, PINK); band(img, 135, g, PURPLE)
        disc(img, 100, g, 38, GOLD, half="top")  # setting sun
        stars(img, [(40, 40), (160, 55), (120, 30)], MOON)
        g = CH - 22
        band(img, g, CH, NAVY); return finish(img)
    elif name == "night":
        band(img, 0, g, NAVY)
        disc(img, 150, 56, 26, MOON)
        disc(img, 140, 50, 24, NAVY)            # carve crescent
        stars(img, [(40, 40), (70, 80), (30, 110), (100, 60),
                    (175, 120), (60, 150), (120, 130), (90, 100)], WHITE)
        band(img, g, CH, (0, 0, 85)); return finish(img)
    band(img, g, CH, GREEN)                     # grassy ground for day scenes
    return finish(img)


# ---------- b&w (woodcut) scenes ----------
def bw_scene(name):
    img = canvas(BW, BH, WHITE)
    horizon = BH - 30
    if name == "night":
        band(img, 0, BH, BLACK)                 # carved-white-on-black woodcut
        disc(img, 104, 44, 20, WHITE)
        disc(img, 96, 38, 18, BLACK)            # crescent
        stars(img, [(30, 30), (55, 60), (24, 80), (74, 28), (120, 70),
                    (44, 110), (90, 92), (118, 110), (66, 130)], WHITE)
        return finish(img)
    line(img, 0, horizon, BW, horizon, BLACK, 2)
    if name == "dawn":
        disc(img, 72, horizon, 22, WHITE)
        ring(img, 72, horizon, 22, BLACK, 2)
        rays(img, 72, horizon, 26, 44, 9, BLACK, 1, span=3.14159, start=3.14159)
        hatch(img, 0, 0, BW, 36, 9, BLACK, 1)
    elif name == "morning":
        ring(img, 44, 46, 18, BLACK, 2); rays(img, 44, 46, 22, 38, 12, BLACK)
        cloud_outline(img, 100, 70, 16); cloud_outline(img, 60, 104, 13)
    elif name == "midday":
        ring(img, 72, 40, 20, BLACK, 2); rays(img, 72, 40, 24, 44, 16, BLACK)
        for bx in (40, 60, 100):                # little birds
            line(img, bx, 96, bx + 6, 92, BLACK); line(img, bx + 6, 92, bx + 12, 96, BLACK)
    elif name == "afternoon":
        ring(img, 104, 58, 18, BLACK, 2); rays(img, 104, 58, 22, 38, 12, BLACK)
        cloud_outline(img, 48, 50, 15); cloud_outline(img, 92, 104, 13)
        hatch(img, 0, 110, BW, horizon, 12, BLACK, 1)
    elif name == "dusk":
        disc(img, 72, horizon, 20, WHITE); ring(img, 72, horizon, 20, BLACK, 2)
        rays(img, 72, horizon, 24, 60, 11, BLACK, 1, span=3.14159, start=3.14159)
        hatch(img, 0, 0, BW, 60, 6, BLACK, 1)   # darkening cross-hatch
        hatch(img, 0, 0, BW, 60, 6, BLACK, 1)
    return finish(img)


def cloud_outline(img, cx, cy, s):
    import math
    pts = [(-s, 0, s), (0, -s // 2, int(s * 1.3)), (s, 0, s)]
    for dx, dy, rr in pts:
        for d in range(0, 360, 3):
            a = math.radians(d)
            px(img, int(cx + dx + rr * math.cos(a)), int(cy + dy + rr * math.sin(a)), BLACK)
    line(img, cx - 2 * s, cy + s // 2, cx + 2 * s, cy + s // 2, WHITE, 3)  # erase underside
    line(img, cx - 2 * s, cy + s // 2, cx + 2 * s, cy + s // 2, BLACK, 1)


# ---------- PNG output ----------
def finish(img):
    return img


def write_png(path, img):
    h, w = len(img), len(img[0])
    raw = bytearray()
    for row in img:
        raw.append(0)
        for r, g, b in row:
            raw += bytes((r, g, b))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
                     chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ("dawn", "morning", "midday", "afternoon", "dusk", "night"):
        write_png(OUT / f"{name}~color.png", color_scene(name))
        write_png(OUT / f"{name}~bw.png", bw_scene(name))
        print(f"  wrote {name}~color.png / {name}~bw.png")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
