#!/usr/bin/env python3
"""VELMARA - THE FLOATING ISLES. A travel poster for a place that does not exist.

A program that draws one 1024x1024 PNG to /output/entry.png: a dusk sky over
a glowing sea, with islands floating in the air, a crystal spire, waterfalls
falling from the sky-islands into the sea below, an airship, and the invented
place's name set large into the picture.

Pure standard library, no network, fully deterministic: two runs produce
identical bytes.
"""
import binascii, os, struct, zlib

W, H = 1024, 1024

# 5x7 font. One glyph per line: seven rows of five bits, space separated.
GLYPHS = {
 "A": "01110 10001 10001 11111 10001 10001 10001",
 "B": "11110 10001 10001 11110 10001 10001 11110",
 "C": "01110 10001 10000 10000 10000 10001 01110",
 "D": "11110 10001 10001 10001 10001 10001 11110",
 "E": "11111 10000 10000 11110 10000 10000 11111",
 "F": "11111 10000 10000 11110 10000 10000 10000",
 "G": "01110 10001 10000 10111 10001 10001 01111",
 "H": "10001 10001 10001 11111 10001 10001 10001",
 "I": "01110 00100 00100 00100 00100 00100 01110",
 "J": "00111 00010 00010 00010 00010 10010 01100",
 "K": "10001 10010 10100 11000 10100 10010 10001",
 "L": "10000 10000 10000 10000 10000 10000 11111",
 "M": "10001 11011 10101 10101 10001 10001 10001",
 "N": "10001 11001 10101 10011 10001 10001 10001",
 "O": "01110 10001 10001 10001 10001 10001 01110",
 "P": "11110 10001 10001 11110 10000 10000 10000",
 "Q": "01110 10001 10001 10001 10101 10010 01101",
 "R": "11110 10001 10001 11110 10100 10010 10001",
 "S": "01111 10000 10000 01110 00001 00001 11110",
 "T": "11111 00100 00100 00100 00100 00100 00100",
 "U": "10001 10001 10001 10001 10001 10001 01110",
 "V": "10001 10001 10001 10001 10001 01010 00100",
 "W": "10001 10001 10001 10101 10101 11011 10001",
 "X": "10001 10001 01010 00100 01010 10001 10001",
 "Y": "10001 10001 01010 00100 00100 00100 00100",
 "Z": "11111 00001 00010 00100 01000 10000 11111",
 "0": "01110 10001 10011 10101 11001 10001 01110",
 "1": "00100 01100 00100 00100 00100 00100 01110",
 "2": "01110 10001 00001 00110 01000 10000 11111",
 "3": "11111 00010 00100 00010 00001 10001 01110",
 "4": "00010 00110 01010 10010 11111 00010 00010",
 "5": "11111 10000 11110 00001 00001 10001 01110",
 "6": "00110 01000 10000 11110 10001 10001 01110",
 "7": "11111 00001 00010 00100 01000 01000 01000",
 "8": "01110 10001 10001 01110 10001 10001 01110",
 "9": "01110 10001 10001 01111 00001 00010 01100",
 " ": "00000 00000 00000 00000 00000 00000 00000",
 ".": "00000 00000 00000 00000 00000 01100 01100",
 ",": "00000 00000 00000 00000 01100 00100 01000",
 ":": "00000 01100 01100 00000 01100 01100 00000",
 "!": "00100 00100 00100 00100 00100 00000 00100",
 "?": "01110 10001 00001 00110 00100 00000 00100",
 "'": "00100 00100 01000 00000 00000 00000 00000",
 "-": "00000 00000 00000 01110 00000 00000 00000",
 "/": "00001 00010 00010 00100 01000 01000 10000",
 "(": "00010 00100 01000 01000 01000 00100 00010",
 ")": "01000 00100 00010 00010 00010 00100 01000",
}
EMPTY_ROWS = ["00000"] * 7


def rows(ch):
    g = GLYPHS.get(ch.upper())
    return g.split(" ") if g else EMPTY_ROWS


def text_w(s, sc):
    return len(s) * 6 * sc


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rect(px, x, y, w, h, col):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    band = bytes(col) * (x1 - x0)
    for yy in range(y0, y1):
        o = (yy * W + x0) * 3
        px[o:o + len(band)] = band


def set_px(px, x, y, col):
    if 0 <= x < W and 0 <= y < H:
        o = (y * W + x) * 3
        px[o:o + 3] = bytes(col)


def line(px, x0, y0, x1, y1, col):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        set_px(px, x0, y0, col)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def disc(px, cx, cy, r, col):
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        half = int((r * r - dy * dy) ** 0.5) if r * r - dy * dy >= 0 else 0
        rect(px, cx - half, yy, half * 2 + 1, 1, col)


def ellipse(px, cx, cy, rx, ry, col):
    for yy in range(cy - ry, cy + ry + 1):
        dy = (yy - cy) / ry
        half = int(rx * (1 - dy * dy) ** 0.5) if 1 - dy * dy >= 0 else 0
        rect(px, cx - half, yy, half * 2 + 1, 1, col)


def tri(px, ax, ay, bx, by, cx, cy, col):
    # filled triangle via scanlines
    pts = sorted([(ax, ay), (bx, by), (cx, cy)], key=lambda p: p[1])
    (x0, y0), (x1, y1), (x2, y2) = pts
    for y in range(y0, y2 + 1):
        if y < y1:
            t1 = (y - y0) / (y1 - y0) if y1 != y0 else 0
            xa = x0 + (x1 - x0) * t1
        else:
            xa = x1
        t2 = (y - y0) / (y2 - y0) if y2 != y0 else 0
        xb = x0 + (x2 - x0) * t2
        if y >= y1:
            t3 = (y - y1) / (y2 - y1) if y2 != y1 else 0
            xa = x1 + (x2 - x1) * t3
        lo, hi = sorted([int(xa), int(xb)])
        rect(px, lo, y, hi - lo + 1, 1, col)


def draw_text(px, s, x, y, sc, col):
    for ch in s:
        for r, bits in enumerate(rows(ch)):
            for c, b in enumerate(bits):
                if b == "1":
                    rect(px, x + c * sc, y + r * sc, sc, sc, col)
        x += 6 * sc


def draw_centred(px, s, cx, y, sc, col):
    draw_text(px, s, cx - text_w(s, sc) // 2, y, sc, col)


def chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF))


def to_png(px):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    body = bytearray()
    stride = W * 3
    for yy in range(H):
        body.append(0)
        body += px[yy * stride:(yy + 1) * stride]
    blob = zlib.compress(bytes(body), 9)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", blob) + chunk(b"IEND", b"")


# palette
SKY_TOP = (22, 14, 58)
SKY_MID = (88, 44, 112)
SKY_LOW = (214, 96, 84)
HORIZON = (255, 176, 96)
SEA_TOP = (16, 84, 104)
SEA_BOT = (6, 38, 66)
CREAM = (255, 240, 208)
GOLD = (255, 196, 110)
ROCK = (74, 52, 66)
ROCK_DARK = (52, 36, 50)
LEAF = (34, 122, 74)
LEAF_DARK = (22, 88, 56)
WATER = (150, 214, 235)
SPIRE = (190, 228, 255)
HOUSE = (255, 214, 150)
ROOF = (168, 52, 60)


def vgrad(px, y0, y1, c0, c1):
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        rect(px, 0, y, W, 1, lerp(c0, c1, t))


def island(px, cx, top, rx, ry, drop, spire=False, houses=0):
    # rock: rounded top + tapering point below
    ellipse(px, cx, top, rx, ry, LEAF)
    ellipse(px, cx, top + 6, rx, ry - 4, ROCK)
    tri(px, cx - rx + 8, top + 10, cx + rx - 8, top + 10, cx, top + drop, ROCK_DARK)
    # grass rim
    ellipse(px, cx, top - 2, rx, ry // 2 + 4, LEAF)
    ellipse(px, cx, top - 4, rx - 30, ry // 2, LEAF_DARK)
    if spire:
        # crystal spire: tall pale triangle with a bright core
        tri(px, cx - 26, top - 10, cx + 26, top - 10, cx, top - 210, SPIRE)
        tri(px, cx - 10, top - 10, cx + 12, top - 10, cx + 2, top - 190, (255, 255, 255))
    for i in range(houses):
        hx = cx - rx // 2 + i * (rx // houses) + 8
        hy = top - 26
        rect(px, hx, hy, 34, 26, HOUSE)
        tri(px, hx - 3, hy, hx + 37, hy, hx + 17, hy - 16, ROOF)
        rect(px, hx + 12, hy + 10, 10, 8, (255, 190, 80))
    # waterfall falling from the island's edge into the sea
    wx = cx + rx - 26
    rect(px, wx, top + 18, 10, 660 - top - 18, WATER)
    rect(px, wx + 3, top + 18, 4, 660 - top - 18, (210, 240, 250))


def bird(px, x, y, s, col):
    line(px, x - s, y, x, y - s // 2, col)
    line(px, x, y - s // 2, x + s, y, col)


def render():
    px = bytearray((0, 0, 0) * (W * H))
    # sky: deep indigo to dusk amber
    vgrad(px, 0, 340, SKY_TOP, SKY_MID)
    vgrad(px, 340, 660, SKY_MID, HORIZON)
    # stars in the upper sky (deterministic LCG)
    seed = 1234567
    for _ in range(90):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sx = seed % W
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sy = seed % 300
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        if seed % 3 == 0:
            rect(px, sx, sy, 2, 2, CREAM)
        else:
            set_px(px, sx, sy, CREAM)
    # small pale moon, high on the right, clear of the spire
    disc(px, 840, 170, 34, (238, 228, 200))
    disc(px, 830, 162, 6, (214, 202, 172))
    disc(px, 850, 180, 4, (214, 202, 172))
    # low sun over the horizon
    disc(px, 720, 560, 118, (255, 150, 80))
    disc(px, 720, 560, 96, (255, 190, 110))
    disc(px, 720, 560, 72, (255, 222, 150))
    # soft clouds
    for cx, cy, rx in [(180, 300, 150), (330, 280, 110), (860, 330, 130), (120, 380, 90)]:
        ellipse(px, cx, cy, rx, 18, (240, 170, 150))
        ellipse(px, cx, cy + 8, rx - 30, 14, (250, 200, 170))
    # airship drifting left of the sun
    ellipse(px, 250, 232, 92, 30, (232, 84, 84))
    ellipse(px, 250, 224, 92, 18, (244, 130, 110))
    rect(px, 222, 264, 56, 16, (90, 50, 60))
    tri(px, 330, 232, 356, 214, 356, 250, (232, 84, 84))
    line(px, 250, 262, 250, 264, (60, 40, 50))
    # birds
    for bx, by, bs in [(420, 200, 16), (470, 225, 12), (620, 180, 14), (150, 180, 12), (850, 210, 15)]:
        bird(px, bx, by, bs, (30, 20, 50))
    # floating islands
    island(px, 170, 430, 110, 26, 130, spire=False, houses=1)
    island(px, 512, 470, 250, 42, 210, spire=True, houses=3)
    island(px, 870, 400, 120, 28, 140, spire=False, houses=1)
    # sea
    vgrad(px, 660, H, SEA_TOP, SEA_BOT)
    # sun reflection shimmer under the sun
    seed = 987654
    for yy in range(668, 1000, 8):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        wdt = 30 + seed % 120
        rect(px, 720 - wdt // 2, yy, wdt, 4, GOLD)
    # wave dashes
    seed = 424242
    for yy in range(690, 980, 34):
        for xx in range(20, W - 20, 46):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            off = seed % 20
            rect(px, xx + off, yy, 26, 3, (120, 200, 220))
    # poster frame
    rect(px, 0, 0, W, 14, CREAM)
    rect(px, 0, H - 14, W, 14, CREAM)
    rect(px, 0, 0, 14, H, CREAM)
    rect(px, W - 14, 0, 14, H, CREAM)
    # title block: name set large into the picture
    draw_centred(px, "VELMARA", W // 2, 44, 13, CREAM)
    rect(px, W // 2 - 300, 148, 600, 4, GOLD)
    draw_centred(px, "THE FLOATING ISLES", W // 2, 166, 4, GOLD)
    # bottom band
    rect(px, 0, 906, W, 118, (14, 10, 40))
    rect(px, 0, 906, W, 4, GOLD)
    draw_centred(px, "WHERE THE SEA LEARNS TO FLY", W // 2, 932, 4, CREAM)
    draw_centred(px, "SAIL BEYOND THE MAP", W // 2, 972, 3, GOLD)
    return px


def main():
    out = "/output/entry.png"
    os.makedirs("/output", exist_ok=True)
    data = to_png(render())
    with open(out, "wb") as fh:
        fh.write(data)
    print("wrote %s (%d bytes)" % (out, len(data)))


if __name__ == "__main__":
    raise SystemExit(main())
