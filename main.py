#!/usr/bin/env python3
"""news-image-20261120: one image summing up the world news of Friday 20 Nov 2026.

Pure Python 3 standard library only (zlib, struct, math, os). No network, no
files read, no randomness: two runs write byte-identical PNGs to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

The picture is a newspaper front page: a masthead naming the day, one lead
story (the first-ever Trump-Xi-Putin three-way summit in Shenzhen), and six
further stories from around the world, each with a small drawn pictogram.
All drawing is done in code on a 1024x1024 RGB canvas, text with an embedded
5x7 bitmap font, PNG encoded by hand.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---- palette ---------------------------------------------------------------
PAPER = (246, 241, 231)
INK = (20, 33, 61)
NAVY = (20, 33, 61)
RED = (178, 34, 34)
BLUE = (29, 78, 137)
GOLD = (217, 164, 65)
WHITE = (255, 255, 255)
PANEL = (255, 255, 255)
BORDER = (206, 200, 184)
GREY = (90, 88, 80)
LIGHT_BLUE = (174, 205, 230)
LIGHT_GOLD = (247, 224, 178)
TEAL = (23, 120, 110)


def _chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(
        ">I", zlib.crc32(body) & 0xFFFFFFFF)


def encode_png(rgb, w, h):
    """Encode a flat RGB bytearray as a PNG (8-bit, colour type 2)."""
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


class Canvas:
    """A flat RGB canvas with a few drawing primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x1 > x0 else -1), (1 if y1 > y0 else -1)
        err, x, y = dx - dy, x0, y0
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x + a, y + b, c)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c, fill=True):
        if fill:
            for yy in range(-r, r + 1):
                half = int(math.sqrt(max(0, r * r - yy * yy)))
                self.fill_rect(cx - half, cy + yy, half * 2 + 1, 1, c)
        else:
            for a in range(360):
                rad = math.radians(a)
                self.set(cx + int(r * math.cos(rad)),
                         cy + int(r * math.sin(rad)), c)

    def ring(self, cx, cy, r, c, t=3):
        for rr in range(r - t + 1, r + 1):
            self.circle(cx, cy, rr, c, fill=False)

# ---- 5x7 bitmap font -------------------------------------------------------
# Each glyph: 7 rows of 5 pixels, '#' on, '.' off. Text is upper-cased first.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ";": ("00000", "01100", "00000", "01100", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10001", "01110", "10101", "01110", "10001", "00000"),
}


def text_w(s, scale):
    """Pixel width of a string at a scale (5 px glyph + 1 px gap)."""
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    """Draw upper-cased text; unknown chars render as space."""
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == "1":
                    cv.fill_rect(cx + c * scale, y + r * scale,
                                 scale, scale, color)
        cx += 6 * scale
    return cx


def wrap_lines(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, s, scale, max_w, color, leading=None):
    """Draw wrapped text; returns the y just below the last line."""
    lh = leading if leading is not None else 10 * scale
    for ln in wrap_lines(s, scale, max_w):
        draw_text(cv, x, y, ln, scale, color)
        y += lh
    return y

# ---- pictograms (drawn, one per story) -------------------------------------
def pic_scales(cv, x, y, s, c):
    """Scales of justice: post, beam, two pans."""
    cv.fill_rect(x + s // 2 - 2, y, 4, s, c)
    cv.fill_rect(x, y + 6, s, 4, c)
    cv.line(x + 4, y + 10, x + 14, y + s - 14, c, 2)
    cv.line(x + s - 4, y + 10, x + s - 14, y + s - 14, c, 2)
    for px in (10, s - 26):
        cv.line(x + px + 2, y + s - 14, x + px + 14, y + s - 14, c, 2)
        cv.line(x + px + 2, y + s - 14, x + px + 8, y + s - 4, c, 2)
        cv.line(x + px + 14, y + s - 14, x + px + 8, y + s - 4, c, 2)


def pic_clock(cv, x, y, s, c):
    cv.ring(x + s // 2, y + s // 2, s // 2 - 4, c, 4)
    cv.line(x + s // 2, y + s // 2, x + s // 2, y + 16, c, 3)
    cv.line(x + s // 2, y + s // 2, x + s - 16, y + s // 2 + 8, c, 3)
    cv.circle(x + s // 2, y + s // 2, 4, c)


def pic_probe(cv, x, y, s, c):
    for sx, sy in ((8, 10), (s - 8, 14), (14, s - 12), (s - 12, s - 8)):
        cv.circle(x + sx, y + sy, 2, GOLD)
    cv.line(x + s // 2, y + s // 2 - 8, x + s // 2 - 14, y + s // 2 + 10, c, 3)
    cv.line(x + s // 2, y + s // 2 - 8, x + s // 2 + 16, y + s // 2 + 6, c, 3)
    cv.circle(x + s // 2, y + s // 2 - 10, 7, c)
    cv.line(x + s // 2 - 6, y + s // 2 - 14, x + s // 2 - 18, y + s // 2 - 26,
            c, 2)
    cv.circle(x + s // 2 - 20, y + s // 2 - 28, 3, RED)


def pic_cyclone(cv, x, y, s, c):
    cx, cy = x + s // 2, y + s // 2
    for k in range(5):
        r = 8 + k * 8
        a0, a1 = k * 70, k * 70 + 250
        for a in range(a0, a1, 4):
            rad = math.radians(a)
            cv.set(cx + int(r * math.cos(rad)), cy + int(r * math.sin(rad)), c)
            cv.set(cx + int(r * math.cos(rad)) + 1,
                   cy + int(r * math.sin(rad)), c)
    cv.circle(cx, cy, 5, RED)


def pic_chart(cv, x, y, s, c):
    base = y + s - 12
    for i, h in enumerate((22, 38, 56)):
        bx = x + 10 + i * 20
        cv.fill_rect(bx, base - h, 14, h, (GOLD, TEAL, RED)[i])
    cv.line(x + 6, base, x + s - 6, base, c, 3)
    cv.line(x + 6, base, x + 6, y + 8, c, 3)


def pic_frame(cv, x, y, s, c):
    cv.rect(x + 8, y + 8, s - 16, s - 16, GOLD, 4)
    cv.fill_rect(x + 12, y + 12, s - 24, s - 24, LIGHT_BLUE)
    cv.circle(x + s - 26, y + 26, 9, GOLD)
    for k in range(3):
        yy = y + s - 26 - k * 10
        cv.line(x + 14, yy, x + s - 14, yy - 6, BLUE, 2)


def pic_flags(cv, x, y, w, h):
    """Three small flags: USA, China, Russia, with labels under each."""
    fw, fh, gap = 74, 46, 14
    # USA: red/white stripes + blue canton
    fx = x
    for i in range(7):
        cv.fill_rect(fx, y + i * (fh // 7), fw, fh // 7,
                     RED if i % 2 == 0 else WHITE)
    cv.fill_rect(fx, y, 30, 20, BLUE)
    # China: red field, gold stars
    fx = x + fw + gap
    cv.fill_rect(fx, y, fw, fh, RED)
    cv.circle(fx + 12, y + 12, 5, GOLD)
    for sx, sy in ((28, 8), (34, 14), (30, 22), (22, 20)):
        cv.circle(fx + sx, y + sy, 2, GOLD)
    # Russia: white / blue / red horizontal
    fx = x + 2 * (fw + gap)
    for i, col in enumerate((WHITE, BLUE, RED)):
        cv.fill_rect(fx, y + i * (fh // 3), fw, fh // 3 + 1, col)
    cv.rect(fx, y, fw, fh, BORDER, 1)
    labels = ("USA", "CHINA", "RUSSIA")
    for i, lab in enumerate(labels):
        lx = x + i * (fw + gap) + (fw - text_w(lab, 2)) // 2
        draw_text(cv, lx, y + fh + 8, lab, 2, GREY)


# ---- panels ------------------------------------------------------------------
def story_panel(cv, x, y, w, h, kicker, kcolor, headline, body, pic):
    cv.fill_rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, h, BORDER, 1)
    cv.fill_rect(x, y, w, 5, kcolor)
    ix, iy, isz = x + 14, y + 26, 84
    cv.fill_rect(ix - 6, iy - 6, isz + 12, isz + 12, PAPER)
    pic(cv, ix, iy, isz, kcolor)
    tx = x + 126
    draw_text(cv, tx, y + 20, kicker, 2, kcolor)
    draw_block(cv, tx, y + 44, headline, 3, w - 140, INK, leading=28)
    n_head = len(wrap_lines(headline, 3, w - 140))
    draw_block(cv, tx, y + 44 + n_head * 28 + 6, body, 2,
               w - 140, GREY, leading=19)

# ---- page layout -------------------------------------------------------------
def masthead(cv):
    cv.fill_rect(0, 0, W, 118, NAVY)
    # small globe, left
    cx, cy, r = 62, 59, 36
    cv.circle(cx, cy, r, BLUE)
    cv.ring(cx, cy, r, GOLD, 3)
    for k in (-14, 0, 14):
        cv.line(cx + k, cy - r + 6, cx + k, cy + r - 6, LIGHT_BLUE, 2)
    cv.line(cx - r + 6, cy - 12, cx + r - 6, cy - 12, LIGHT_BLUE, 2)
    cv.line(cx - r + 6, cy + 12, cx + r - 6, cy + 12, LIGHT_BLUE, 2)
    draw_text(cv, 120, 26, "THE WORLD IN ONE IMAGE", 5, WHITE)
    draw_text(cv, 120, 80, "FRIDAY - 20 NOVEMBER 2026", 3, GOLD)


def lead_story(cv):
    x, y, w, h = 24, 134, 976, 252
    cv.fill_rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, h, BORDER, 1)
    cv.fill_rect(x, y, w, 5, RED)
    draw_text(cv, x + 24, y + 18, "SHENZHEN, CHINA - THE LEAD STORY", 2, RED)
    hx = x + 24
    y2 = draw_block(cv, hx, y + 48, "Trump, Xi and Putin hold historic "
                    "first three-way summit", 4, 660, INK, leading=40)
    draw_block(cv, hx, y2 + 8, "The three leaders met in Shenzhen and "
               "released a joint peace declaration on nuclear risks and "
               "global security.", 2, 660, GREY, leading=19)
    pic_flags(cv, x + w - 24 - 250, y + 48, 250, 46)
    tx, ty, tw, th = x + w - 24 - 250, y + 48 + 46 + 30, 250, 30
    cv.fill_rect(tx, ty, tw, th, RED)
    label = "PEACE DECLARATION"
    draw_text(cv, tx + (tw - text_w(label, 2)) // 2, ty + 8, label, 2, WHITE)


STORIES = [
    ("THE HAGUE", RED, pic_scales, "Myanmar guilty of genocide",
     "UN court: Myanmar committed genocide against the Rohingya."),
    ("WASHINGTON", BLUE, pic_clock, "Trump: no rush on Iran",
     "President pushes any Iran decision to 2027: see what happens "
     "after Jan 1."),
    ("SPACE", NAVY, pic_probe, "Voyager 1: one light-day out",
     "NASA confirms the probe is now a light-day from Earth, the "
     "farthest ever."),
    ("ODISHA, INDIA", TEAL, pic_cyclone, "Cyclone Akvan hits Odisha",
     "300,000 evacuated as the storm nears India's east coast. "
     "423 rescue teams out."),
    ("ENTERTAINMENT", BLUE, pic_chart, "GTA 6 sales pass $1.8bn",
     "Sales top $1.8 billion, already past The Odyssey's global "
     "box-office run."),
    ("ART MARKET", RED, pic_frame, "Van Gogh: record $190.4m sale",
     "A Van Gogh sells for a record $190.4m after a row over its "
     "Nazi-era history."),
]


def build():
    cv = Canvas(W, H, PAPER)
    masthead(cv)
    lead_story(cv)
    for i, (kicker, color, pic, head, body) in enumerate(STORIES):
        px = 24 + (i % 2) * 500
        py = 402 + (i // 2) * 196
        story_panel(cv, px, py, 476, 180, kicker, color, head, body, pic)
    cv.fill_rect(24, 982, 976, 2, BORDER)
    foot = "FRIDAY 20 NOVEMBER 2026 - THE WORLD IN ONE IMAGE - MAKE.FUN"
    draw_text(cv, (W - text_w(foot, 2)) // 2, 996, foot, 2, GREY)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = encode_png(build().px, W, H)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(data), W, H))


if __name__ == "__main__":
    main()
