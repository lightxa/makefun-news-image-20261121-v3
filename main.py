# news-image-20261121, variant 3: an atlas of Saturday 21 November 2026.
# A dark ink-charcoal world map with numbered amber pins, and six short
# story cards below it. Pure Python standard library, no network, fully
# deterministic: the same run always writes the same bytes.
#
# The image is drawn pixel by pixel into an RGB buffer (a small embedded
# 5x7 bitmap font renders all text) and encoded as PNG by hand with zlib.

import os
import struct
import zlib

W, H = 1024, 1024

# --- palette: ink charcoal, warm amber, off-white ---------------------------
INK = (27, 27, 34)        # page background
INK2 = (34, 34, 44)       # map panel background
LAND = (74, 84, 106)      # continent fill, muted slate blue
LAND_EDGE = (150, 158, 178)
GRID = (48, 48, 60)       # faint graticule
AMBER = (232, 163, 61)    # warm amber accent
AMBER_DK = (198, 132, 32)
OFFWHITE = (245, 239, 227)
MUTED = (178, 172, 158)   # secondary text
FAINT = (120, 116, 104)
RULE = (64, 64, 76)
PIN_NUM = (27, 27, 34)    # number inside the amber pin


def chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def encode_png(rgb, w, h):
    """Encode an RGB byte string as a deterministic PNG (filter 0 rows)."""
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    return png


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.set(x, y, color)

    def hline(self, x0, x1, y, color, thick=1):
        for t in range(thick):
            for x in range(x0, x1):
                self.set(x, y + t, color)

    def vline(self, x, y0, y1, color, thick=1):
        for t in range(thick):
            for y in range(y0, y1):
                self.set(x + t, y, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, color)

    def ring(self, cx, cy, r, color, thick=2):
        for y in range(cy - r - thick, cy + r + thick + 1):
            for x in range(cx - r - thick, cx + r + thick + 1):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if r - thick < d <= r:
                    self.set(x, y, color)

    def poly(self, pts, color):
        """Scanline fill of a simple polygon."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, color)

    def polyline(self, pts, color, closed=True):
        seq = pts + [pts[0]] if closed else pts
        for i in range(len(seq) - 1):
            self.line(seq[i][0], seq[i][1], seq[i + 1][0], seq[i + 1][1], color)


# --- 5x7 bitmap font (all text in the image is uppercase) -------------------
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is empty.
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
}

FONT.update({
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "\u2022": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
})


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color, bold=False):
    """Draw uppercase text; returns the x just past the last glyph."""
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == "1":
                    cv.rect(x + col * scale, y + row * scale,
                            x + (col + 1) * scale, y + (row + 1) * scale, color)
                    if bold:
                        cv.rect(x + col * scale + 1, y + row * scale,
                                x + (col + 1) * scale + 1, y + (row + 1) * scale, color)
        x += 6 * scale
    return x


def draw_centered(cv, cx, y, s, scale, color, bold=False):
    draw_text(cv, cx - text_width(s, scale) // 2, y, s, scale, color, bold)


def wrap(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

# --- the world map: schematic continents in (lon, lat) ----------------------
MAP_X0, MAP_Y0, MAP_X1, MAP_Y1 = 36, 168, 988, 528


def project(lon, lat):
    x = MAP_X0 + (lon + 168) / 350.0 * (MAP_X1 - MAP_X0)
    y = MAP_Y0 + (78 - lat) / 136.0 * (MAP_Y1 - MAP_Y0)
    return (int(round(x)), int(round(y)))


CONTINENTS = [
    # North America
    [(-168, 66), (-165, 60), (-158, 58), (-152, 60), (-140, 60), (-135, 58),
     (-130, 54), (-125, 49), (-124, 42), (-120, 34), (-117, 33), (-112, 29),
     (-110, 24), (-105, 20), (-97, 16), (-94, 17), (-90, 14), (-86, 12),
     (-83, 9), (-80, 8), (-78, 9), (-81, 13), (-84, 16), (-87, 21),
     (-90, 21), (-91, 19), (-97, 26), (-93, 30), (-89, 30), (-84, 30),
     (-81, 26), (-80, 32), (-76, 35), (-74, 40), (-70, 42), (-68, 45),
     (-65, 44), (-60, 47), (-55, 47), (-60, 52), (-65, 55), (-68, 58),
     (-72, 62), (-78, 62), (-85, 66), (-92, 66), (-95, 69), (-110, 68),
     (-125, 70), (-140, 70), (-155, 71), (-162, 70)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-40, 65), (-32, 68), (-22, 70),
     (-25, 76), (-40, 80), (-58, 76), (-60, 70)],
    # South America
    [(-78, 7), (-75, 10), (-72, 12), (-64, 11), (-60, 8), (-55, 6),
     (-52, 4), (-50, 0), (-44, -3), (-40, -5), (-35, -8), (-38, -15),
     (-40, -22), (-48, -28), (-52, -33), (-58, -38), (-62, -41), (-65, -45),
     (-68, -50), (-69, -52), (-72, -54), (-74, -50), (-73, -44), (-73, -37),
     (-71, -30), (-70, -23), (-70, -18), (-75, -15), (-77, -12), (-80, -6),
     (-81, -2), (-80, 1)],
    # Africa
    [(-17, 15), (-16, 20), (-13, 27), (-10, 31), (-6, 35), (0, 36),
     (10, 37), (11, 34), (20, 32), (30, 31), (32, 31), (35, 28), (37, 22),
     (39, 18), (43, 12), (48, 11), (51, 12), (46, 5), (42, 0), (40, -5),
     (40, -10), (38, -15), (35, -20), (33, -26), (28, -33), (20, -35),
     (16, -28), (13, -20), (12, -12), (13, -6), (9, -1), (9, 4), (4, 6),
     (-8, 5), (-13, 8)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (44, -25),
     (43, -21)],
    # Eurasia
    [(-9, 37), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 50), (2, 51),
     (5, 53), (8, 57), (5, 59), (10, 59), (12, 55), (18, 56), (21, 55),
     (24, 58), (21, 60), (24, 62), (28, 66), (30, 70), (35, 68), (40, 68),
     (45, 68), (55, 69), (65, 69), (70, 72), (75, 72), (80, 73), (90, 75),
     (100, 77), (110, 74), (120, 73), (130, 72), (140, 72), (150, 70),
     (160, 70), (170, 67), (178, 65), (173, 64), (170, 60), (162, 60),
     (158, 56), (162, 52), (158, 50), (150, 59), (142, 55), (142, 50),
     (140, 45), (138, 40), (135, 35), (130, 33), (127, 35), (126, 38),
     (122, 39), (120, 35), (118, 30), (112, 22), (109, 18), (105, 10),
     (104, 8), (100, 6), (98, 10), (95, 16), (92, 21), (89, 22), (86, 20),
     (80, 15), (77, 8), (75, 12), (73, 18), (70, 22), (66, 25), (61, 25),
     (57, 27), (54, 26), (52, 28), (50, 29), (48, 30), (44, 29), (40, 31),
     (36, 36), (33, 36), (30, 36), (27, 37), (23, 36), (22, 38), (19, 40),
     (16, 40), (12, 44), (8, 44), (3, 43)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-2, 58), (0, 53), (1, 51)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (138, 35), (140, 38), (141, 41),
     (143, 43), (141, 45), (140, 44), (138, 40), (136, 37), (133, 35)],
    # New Guinea
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -8), (147, -9),
     (143, -8), (138, -8), (134, -4)],
    # Borneo
    [(109, 1), (113, 4), (117, 6), (119, 1), (117, -3), (113, -4), (110, -2)],
    # Sumatra
    [(95, 5), (98, 3), (101, 0), (104, -3), (106, -5), (104, -4),
     (100, -1), (97, 2)],
    # Australia
    [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33), (129, -32),
     (132, -32), (135, -35), (137, -35), (140, -38), (145, -38), (147, -39),
     (150, -37), (153, -32), (153, -27), (150, -23), (146, -19), (142, -15),
     (142, -11), (137, -12), (135, -15), (132, -12), (130, -13), (126, -14),
     (122, -17), (118, -20)],
    # New Zealand
    [(167, -45), (168, -44), (170, -43), (172, -41), (174, -39), (175, -38),
     (177, -38), (175, -40), (173, -42), (171, -44), (169, -46)],
    [(166, -46), (168, -46), (170, -47), (168, -48), (166, -47)],
]

# Stories: (pin lon, pin lat, label, label dx, label dy, kicker, headline, body)
# All facts verified against at least two reputable sources in this session:
# COP31 (Reuters, UN News); Bolsonaro (Reuters, CNN); Wellington Test
# (Wisden, myKhel); Elantra (Hyundai Motor Group, Kelley Blue Book);
# NSE (ANI, Angel One); Cyclone Akvan (Hindu BusinessLine, Sambad).
STORIES = [
    (30.7, 36.9, "ANTALYA", 18, -6,
     "CLIMATE - ANTALYA",
     "COP31 TALKS RUN INTO OVERTIME",
     "TALKS IN ANTALYA PASS THEIR DEADLINE AS THE DRAFT DEAL DROPS EVERY "
     "MENTION OF FOSSIL FUELS."),
    (-47.9, -15.8, "BRASILIA", -118, -6,
     "BRAZIL - BRASILIA",
     "BOLSONARO TAKEN TO HOSPITAL",
     "EX-PRESIDENT BOLSONARO, 71, IS IN HOSPITAL WITH SEVERE ABDOMINAL "
     "PAIN AND A BLOCKED INTESTINE."),
    (174.8, -41.3, "WELLINGTON", -140, -6,
     "CRICKET - WELLINGTON",
     "INDIA FIGHT BACK IN WELLINGTON",
     "JAISWAL HITS 85 AND RAHUL 52 NOT OUT AS INDIA REACH 159 FOR 1 ON "
     "DAY TWO IN WELLINGTON."),
    (-118.2, 34.0, "LOS ANGELES", 18, -6,
     "MOTORING - LOS ANGELES",
     "NEW ELANTRA DEBUTS IN LA",
     "HYUNDAI UNVEILS THE EIGHTH-GENERATION ELANTRA AT THE LA AUTO SHOW; "
     "A HYBRID FOLLOWS FOR 2028."),
    (72.9, 19.1, "MUMBAI", -16, -24,
     "MARKETS - MUMBAI",
     "NSE PASSES NASDAQ FOR FIFTH PLACE",
     "INDIA'S NSE PASSES NASDAQ AND HKEX TO BECOME THE WORLD'S "
     "FIFTH-LARGEST LISTED EXCHANGE."),
    (88.0, 17.0, "GOPALPUR", 18, -6,
     "WEATHER - BAY OF BENGAL",
     "CYCLONE AKVAN WEAKENS",
     "THE STORM MAKES LANDFALL NEAR GOPALPUR, THEN FADES AS HEAVY RAIN "
     "MOVES INLAND."),
]


def draw_map(cv):
    cv.rect(MAP_X0, MAP_Y0, MAP_X1, MAP_Y1, INK2)
    # graticule
    for lon in range(-150, 181, 30):
        x, _ = project(lon, 0)
        cv.vline(x, MAP_Y0, MAP_Y1, GRID)
    for lat in (60, 30, 0, -30):
        _, y = project(0, lat)
        cv.hline(MAP_X0, MAP_X1, y, GRID)
    # ocean labels
    draw_centered(cv, *project(-150, 10), "PACIFIC", 2, FAINT)
    draw_centered(cv, *project(-35, 15), "ATLANTIC", 2, FAINT)
    draw_centered(cv, *project(72, -35), "INDIAN OCEAN", 2, FAINT)
    # continents
    for poly_lonlat in CONTINENTS:
        pts = [project(lon, lat) for lon, lat in poly_lonlat]
        cv.poly(pts, LAND)
        cv.polyline(pts, LAND_EDGE)
    # pins and their place labels
    for i, (lon, lat, label, dx, dy, *_rest) in enumerate(STORIES, start=1):
        px, py = project(lon, lat)
        cv.ring(px, py, 15, AMBER, 2)
        cv.circle(px, py, 13, AMBER)
        draw_centered(cv, px, py - 7, str(i), 2, PIN_NUM, bold=True)
        draw_text(cv, px + dx, py + dy, label, 2, OFFWHITE)
    # map frame
    cv.hline(MAP_X0, MAP_X1, MAP_Y0, RULE, 2)
    cv.hline(MAP_X0, MAP_X1, MAP_Y1 - 2, RULE, 2)
    cv.vline(MAP_X0, MAP_Y0, MAP_Y1, RULE, 2)
    cv.vline(MAP_X1 - 2, MAP_Y0, MAP_Y1, RULE, 2)


def draw_stories(cv):
    col_x = [36, 360, 684]
    row_y = [560, 756]
    cell_w = 304
    for idx, story in enumerate(STORIES):
        _lon, _lat, _label, _dx, _dy, kicker, headline, body = story
        x = col_x[idx % 3]
        y = row_y[idx // 3]
        n = idx + 1
        cv.hline(x, x + cell_w, y - 10, AMBER, 3)
        cv.circle(x + 11, y + 8, 11, AMBER)
        draw_centered(cv, x + 11, y + 1, str(n), 2, PIN_NUM, bold=True)
        draw_text(cv, x + 30, y + 1, kicker, 2, AMBER)
        lines = wrap(headline, 3, cell_w)
        hy = y + 32
        for ln in lines:
            draw_text(cv, x, hy, ln, 3, OFFWHITE, bold=True)
            hy += 24
        by = hy + 6
        for ln in wrap(body, 2, cell_w):
            draw_text(cv, x, by, ln, 2, MUTED)
            by += 17


def draw():
    cv = Canvas(W, H, INK)
    # header
    draw_centered(cv, 512, 26, "THE WORLD IN ONE DAY", 3, AMBER)
    draw_centered(cv, 512, 60, "SATURDAY 21 NOVEMBER 2026", 5, OFFWHITE, bold=True)
    cv.hline(212, 812, 122, AMBER, 3)
    draw_centered(cv, 512, 136, "SIX STORIES FROM AROUND THE PLANET", 2, MUTED)
    draw_map(cv)
    draw_stories(cv)
    # footer
    cv.hline(36, 988, 954, RULE, 2)
    draw_centered(cv, 512, 972, "ONE DAY \u2022 ONE WORLD \u2022 SATURDAY 21 NOVEMBER 2026",
                  2, AMBER)
    return encode_png(bytes(cv.buf), W, H)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(draw())


if __name__ == "__main__":
    main()
