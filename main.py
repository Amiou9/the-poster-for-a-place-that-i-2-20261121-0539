#!/usr/bin/env python3
"""AURELIA -- travel poster for a place that does not exist.

Draws a 768x1024 travel poster in pure Python (stdlib only, no Pillow):
floating rock isles in a twilight sky, with waterfalls that fall UPWARD
into the clouds, a low golden sun, and a calm violet sea below.
The place name AURELIA is set into the picture in a large embedded
5x7 bitmap font. Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR).
Deterministic: no randomness, no time, no network.
"""
import math
import os
import struct
import zlib

W, H = 768, 1024
HORIZON = 720

# ---------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)


def row_fill(y, color):
    """Fill a whole scanline with one colour."""
    if 0 <= y < H:
        buf[y * W * 3:(y + 1) * W * 3] = bytes(color) * W


def span(y, x0, x1, color):
    """Fill [x0, x1) on scanline y with one colour (clipped)."""
    if y < 0 or y >= H:
        return
    x0 = max(0, int(x0))
    x1 = min(W, int(x1))
    if x1 <= x0:
        return
    i = (y * W + x0) * 3
    buf[i:i + (x1 - x0) * 3] = bytes(color) * (x1 - x0)


def rect(x, y, w, h, color):
    for yy in range(y, y + h):
        span(yy, x, x + w, color)


def disc(cx, cy, r, color):
    """Filled circle, via per-row spans."""
    r = int(r)
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        span(cy + dy, cx - dx, cx + dx + 1, color)


def disc_upto(cx, cy, r, color, ymax):
    """Filled circle, clipped to rows above ymax (keeps glow out of the sea)."""
    r = int(r)
    for dy in range(-r, r + 1):
        if cy + dy >= ymax:
            continue
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        span(cy + dy, cx - dx, cx + dx + 1, color)


def ellipse(cx, cy, rx, ry, color):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy / ry) ** 2
        dx = int(rx * math.sqrt(max(0.0, t)))
        span(cy + dy, cx - dx, cx + dx + 1, color)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def gradient_rows(stops):
    """stops: [(y, (r,g,b)), ...] sorted by y. Returns list of colours."""
    rows = []
    for y in range(H):
        if y <= stops[0][0]:
            rows.append(stops[0][1])
        elif y >= stops[-1][0]:
            rows.append(stops[-1][1])
        else:
            for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
                if y0 <= y <= y1:
                    rows.append(lerp(c0, c1, (y - y0) / (y1 - y0)))
                    break
    return rows


# ---------------------------------------------------------------- sky + sea
SKY = [(0, (26, 13, 54)), (260, (66, 31, 102)), (480, (128, 56, 106)),
       (620, (208, 104, 70)), (HORIZON, (228, 146, 88))]
SEA = [(HORIZON, (172, 100, 64)), (800, (62, 86, 94)),
       (1024, (20, 28, 60))]

sky_rows = gradient_rows(SKY)
sea_rows = gradient_rows(SEA)
for y in range(HORIZON):
    row_fill(y, sky_rows[y])
for y in range(HORIZON, H):
    row_fill(y, sea_rows[y])

# ---------------------------------------------------------------- clouds
# soft pale ellipses, colours close to the sky at their height
for (cx, cy, rx, ry, col) in [
        (150, 250, 130, 22, (112, 64, 118)),
        (620, 210, 150, 26, (100, 58, 112)),
        (560, 330, 100, 16, (152, 96, 118)),
        (120, 420, 95, 15, (140, 84, 116)),
        (700, 470, 80, 13, (172, 110, 110)),
        (330, 180, 95, 17, (106, 62, 114)),
]:
    ellipse(cx, cy, rx, ry, col)

# ---------------------------------------------------------------- sun + glow
for r, col in [(150, (238, 168, 108)), (118, (244, 188, 122)),
               (92, (250, 206, 134)), (74, (252, 222, 152))]:
    disc_upto(545, 640, r, col, HORIZON - 2)
disc(545, 640, 58, (255, 233, 172))

# ---------------------------------------------------------------- islands
def poly_spans(poly, y):
    """x-intervals of polygon `poly` on scanline y."""
    xs = []
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if y0 == y1:
            continue
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def island(poly, body, top_col, lit_col):
    top_y = min(y for _, y in poly)
    bot_y = max(y for _, y in poly)
    for y in range(top_y, bot_y + 1):
        for x0, x1 in poly_spans(poly, y):
            col = top_col if y < top_y + 12 else body
            span(y, x0, x1 + 1, col)
    # rock strata: a few lighter bands across the underside
    for y in range(top_y + 26, bot_y, 22):
        for x0, x1 in poly_spans(poly, y):
            span(y, x0 + 8, x1 - 7, (50, 76, 68))
    # warm lit rim along the top edge
    for y in range(top_y, top_y + 3):
        for x0, x1 in poly_spans(poly, y):
            span(y, x0, x1 + 1, lit_col)


BODY = (40, 62, 56)
TOP = (76, 106, 88)
LIT = (216, 166, 92)

GREAT = [(170, 470), (590, 470), (520, 540), (430, 600),
         (380, 626), (330, 590), (230, 540)]
LEFT = [(62, 332), (212, 332), (180, 378), (135, 420), (96, 378)]
RIGHT = [(578, 302), (728, 302), (694, 348), (655, 392), (614, 348)]
FAR = [(300, 242), (402, 242), (372, 276), (350, 302), (328, 276)]

for poly in (FAR, LEFT, RIGHT, GREAT):
    island(poly, BODY, TOP, LIT)

# tiny pine silhouettes on the great island's top
for (tx, th) in [(210, 16), (250, 22), (300, 14), (470, 20), (520, 15)]:
    for dy in range(th):
        wdt = max(1, int((th - dy) * 0.55))
        span(470 - dy, tx - wdt, tx + wdt + 1, (22, 34, 30))

# ---------------------------------------------------------------- waterfalls, falling UP
def upward_fall(cx, y_base, y_top, w_base, sway):
    """A bright stream rising from (cx, y_base) to y_top, curving gently."""
    for y in range(y_top, y_base + 1):
        t = (y_base - y) / max(1, y_base - y_top)  # 0 at base, 1 at top
        x = cx + int(sway * math.sin(t * 2.2))
        wdt = max(2, int(w_base * (1.0 - 0.55 * t)))
        span(y, x - wdt, x + wdt + 1, (226, 206, 158))
        span(y, x - max(1, wdt // 2), x + max(1, wdt // 2) + 1,
             (255, 242, 204))
        # droplets breaking off near the top
        if y % 23 == 0 and t > 0.55:
            disc(x + (wdt + 6 if (y // 23) % 2 else -(wdt + 6)), y, 2,
                 (255, 242, 204))


# the great island's upward falls -- the landmark
upward_fall(268, 470, 230, 7, 22)
upward_fall(382, 470, 210, 8, -18)
upward_fall(498, 470, 238, 6, 16)
# smaller falls from the side isles
upward_fall(138, 332, 240, 5, 10)
upward_fall(652, 302, 226, 5, -10)

# mist where the falls leave the rock
for (cx, cy) in [(268, 468), (382, 468), (498, 468), (138, 330), (652, 300)]:
    ellipse(cx, cy, 16, 5, (240, 224, 180))

# ---------------------------------------------------------------- sun path on the sea
for y in range(HORIZON + 2, H):
    t = (y - HORIZON) / (H - HORIZON)
    hw = int(12 + 18 * t + 8 * math.sin(y * 0.05))
    span(y, 545 - hw, 545 + hw + 1, (226, 164, 92))
    span(y, 545 - hw // 2, 545 + hw // 2 + 1, (244, 196, 120))

# wave lines
for y in range(748, H, 30):
    x = 36 + ((y * 13) % 90)
    while x < W - 60:
        ln = 34 + ((y + x) % 46)
        span(y, x, x + ln, (74, 122, 122))
        x += ln + 52

# ---------------------------------------------------------------- birds
def bird(cx, cy, s):
    for i in range(s):
        span(cy + i // 2, cx - i, cx - i + 1, (28, 18, 48))
        span(cy + i // 2, cx + i, cx + i + 1, (28, 18, 48))


for (bx, by, bs) in [(180, 300, 9), (230, 268, 7), (600, 380, 8),
                     (90, 540, 7), (690, 560, 9)]:
    bird(bx, by, bs)

# ---------------------------------------------------------------- name: AURELIA
FONT = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'I': ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
}


def draw_text(text, x0, y0, scale, color):
    x = x0
    for ch in text:
        glyph = FONT[ch]
        for r, bits in enumerate(glyph):
            for c, bit in enumerate(bits):
                if bit == '1':
                    rect(x + c * scale, y0 + r * scale, scale, scale, color)
        x += 6 * scale


NAME = "AURELIA"
SCALE = 14
text_w = len(NAME) * 6 * SCALE - SCALE
tx = (W - text_w) // 2
ty = 92
draw_text(NAME, tx + 5, ty + 6, SCALE, (22, 9, 44))       # shadow
draw_text(NAME, tx, ty, SCALE, (255, 233, 176))           # cream-gold
# (no rule, no tagline: the name alone carries the poster)

# ---------------------------------------------------------------- PNG encoder (stdlib only)


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_png(path):
    raw = b"".join(
        b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(raw, 6))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path)
    print(f"wrote {path} {W}x{H} {size} bytes")


if __name__ == "__main__":
    main()
