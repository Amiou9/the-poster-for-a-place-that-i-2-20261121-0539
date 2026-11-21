#!/usr/bin/env python3
"""ZENTHIA -- travel poster for a place that does not exist.

Draws a 768x1024 travel poster in pure Python (stdlib only, no Pillow):
a glass desert under twin suns, where a colossal hourglass pours its
sand UPWARD into the sky. The place name ZENTHIA is set into the picture
in a large embedded 5x7 bitmap font. Writes /output/entry.png
(or $MAKEFUN_OUTPUT_DIR). Deterministic: no randomness, no time, no network.
"""
import math
import os
import struct
import zlib

W, H = 768, 1024

FONT = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'C': ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'G': ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    'J': ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    'N': ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'Q': ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'V': ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    'W': ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    'X': ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    'Y': ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


class Poster:
    def __init__(self):
        self.buf = bytearray(W * H * 3)

    def span(self, y, x0, x1, col):
        if y < 0 or y >= H:
            return
        x0 = max(0, int(x0)); x1 = min(W, int(x1))
        if x1 <= x0:
            return
        i = (y * W + x0) * 3
        self.buf[i:i + (x1 - x0) * 3] = bytes(col) * (x1 - x0)

    def row(self, y, col):
        self.buf[y * W * 3:(y + 1) * W * 3] = bytes(col) * W

    def rect(self, x, y, w, h, col):
        for yy in range(y, y + h):
            self.span(yy, x, x + w, col)

    def disc(self, cx, cy, r, col):
        r = int(r)
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.span(cy + dy, cx - dx, cx + dx + 1, col)

    def ellipse(self, cx, cy, rx, ry, col):
        for dy in range(-ry, ry + 1):
            dx = int(rx * math.sqrt(max(0.0, 1.0 - (dy / ry) ** 2)))
            self.span(cy + dy, cx - dx, cx + dx + 1, col)

    def disc_upto(self, cx, cy, r, col, ymax):
        r = int(r)
        for dy in range(-r, r + 1):
            if cy + dy >= ymax:
                continue
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.span(cy + dy, cx - dx, cx + dx + 1, col)

    @staticmethod
    def _lerp(a, b, t):
        return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

    def gradient(self, stops, y0=0, y1=H):
        for y in range(y0, min(y1, H)):
            if y <= stops[0][0]:
                c = stops[0][1]
            elif y >= stops[-1][0]:
                c = stops[-1][1]
            else:
                c = stops[-1][1]
                for (ya, ca), (yb, cb) in zip(stops, stops[1:]):
                    if ya <= y <= yb:
                        c = self._lerp(ca, cb, (y - ya) / (yb - ya))
                        break
            self.row(y, c)

    @staticmethod
    def _spans(poly, y):
        xs = []
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % n]
            if y0 == y1:
                continue
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]

    def poly(self, poly, col):
        for y in range(min(y for _, y in poly), max(y for _, y in poly) + 1):
            for x0, x1 in self._spans(poly, y):
                self.span(y, x0, x1 + 1, col)

    def line(self, x0, y0, x1, y1, w, col):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            t = i / steps
            self.disc(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t),
                      max(1, w // 2), col)

    def bird(self, cx, cy, s):
        for i in range(s):
            self.span(cy + i // 2, cx - i, cx - i + 1, (30, 20, 50))
            self.span(cy + i // 2, cx + i, cx + i + 1, (30, 20, 50))

    def text(self, s, scale, shadow, main, ty=92):
        tw = len(s) * 6 * scale - scale
        tx = (W - tw) // 2
        for ox, oy, col in [(5, 6, shadow), (0, 0, main)]:
            x = tx + ox
            for ch in s:
                for r, bits in enumerate(FONT[ch]):
                    for c, bit in enumerate(bits):
                        if bit == '1':
                            self.rect(x + c * scale, ty + oy + r * scale,
                                      scale, scale, col)
                x += 6 * scale

    def png(self, path):
        raw = b"".join(b"\x00" + bytes(self.buf[y * W * 3:(y + 1) * W * 3])
                       for y in range(H))

        def chunk(kind, data):
            out = struct.pack(">I", len(data)) + kind + data
            return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

        data = b"\x89PNG\r\n\x1a\n"
        data += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
        data += chunk(b"IDAT", zlib.compress(raw, 6))
        data += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(data)
        return len(data)


def draw():
    """ZENTHIA: glass desert under twin suns; a colossal hourglass
    pouring sand UPWARD into the sky."""
    p = Poster()
    p.gradient([(0, (176, 88, 40)), (350, (228, 148, 70)),
                (640, (250, 205, 135)), (1024, (250, 205, 135))], 0, 640)
    # twin suns (below the name, clear of the letters)
    for (sx, sy, r) in [(200, 320, 46), (310, 280, 34)]:
        for rr, c in [(r + 52, (244, 190, 120)), (r + 26, (250, 210, 140))]:
            p.disc_upto(sx, sy, rr, c, 640)
        p.disc(sx, sy, r, (255, 242, 192))
    # dunes (sampled sine ridges as polygons); fill the sand first so no
    # black strip shows between the sky and the first ridge
    for y in range(640, H):
        p.row(y, (222, 162, 82))

    def dune(ybase, amp, per, col):
        pts = [(x, int(ybase + amp * math.sin(x * 2 * math.pi / per)))
               for x in range(0, W + 1, 32)]
        p.poly(pts + [(W, H), (0, H)], col)

    dune(660, 26, 700, (222, 162, 82))
    dune(780, 34, 560, (176, 108, 48))
    dune(900, 30, 640, (140, 82, 34))
    # hourglass frame
    p.rect(336, 360, 10, 244, (62, 36, 20))
    p.rect(422, 360, 10, 244, (62, 36, 20))
    p.rect(336, 352, 96, 10, (62, 36, 20))
    p.rect(336, 602, 96, 10, (62, 36, 20))
    # glass bulbs + sand
    p.poly([(346, 362), (422, 362), (384, 472)], (255, 230, 180))
    p.poly([(346, 602), (422, 602), (384, 472)], (255, 230, 180))
    p.poly([(362, 382), (406, 382), (384, 448)], (232, 182, 92))
    p.poly([(360, 592), (408, 592), (384, 512)], (232, 182, 92))
    # sand pouring UP out of the hourglass into the sky
    for y in range(180, 352):
        t = (352 - y) / 172
        x = 384 + int(10 * math.sin(t * 2.4))
        wdt = max(2, int(6 * (1 - 0.5 * t)))
        p.span(y, x - wdt, x + wdt + 1, (244, 200, 110))
        p.span(y, x - 2, x + 3, (255, 232, 160))
        if y % 29 == 0 and t > 0.5:
            p.disc(x + 10, y, 2, (255, 232, 160))
    # rocks + a lone dead tree
    p.ellipse(150, 830, 46, 18, (110, 62, 26))
    p.ellipse(620, 880, 60, 20, (110, 62, 26))
    p.line(620, 880, 620, 800, 6, (70, 42, 20))
    p.line(620, 830, 580, 790, 4, (70, 42, 20))
    p.line(620, 820, 662, 786, 4, (70, 42, 20))
    for (bx, by, bs) in [(520, 300, 8), (470, 340, 7), (150, 420, 8)]:
        p.bird(bx, by, bs)
    p.text("ZENTHIA", 14, (70, 35, 15), (255, 240, 200))
    return p


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = draw().png(path)
    print(f"wrote {path} {W}x{H} {size} bytes")


if __name__ == "__main__":
    main()
