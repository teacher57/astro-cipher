"""Encode text into an astro cipher constellation JPG.

    python encode.py "Лагерь Маши" -o out/lager.jpg [--seed 7]

Each word is a chain of big stars; each line between two big stars is one letter.
The first star of every word has the word's number written next to it in Roman numerals
(I for the first word, then II, III, ...).
"""
import argparse
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree

import alphabet as ab

INK = (245, 245, 245)           # white stars and lines ...
PAPER = (5, 6, 12)              # ... on a black sky
LINE_W = 1.8                    # main lines and roof / vee strokes
THIN_W = 1.4                    # dashes and zigzag pieces between top stars
SS = 3  # supersampling factor for smooth lines

EDGE = 380                      # distance between the two big stars of a letter (key sheet)
EDGE_RANGE = (250, 900)         # ... or a random distance in this range (messages)
BIG_RX, BIG_RY = 18, 24         # big star half-width / half-height
SMALL_RX, SMALL_RY = 7, 9.5     # small star half-width / half-height
LINE_GAP = 44                   # line stops this far from a big star's center
OFFSET = 28                     # small stars sit this far off the line
SPACING = 24                    # gap between small stars in one slot
END_SLOT = 62                   # start / end slot stars sit this far along from their big star


def slot_center(pos, L):
    """Where slot S / M / E sits along a line of length L."""
    return {"S": END_SLOT, "M": L / 2, "E": L - END_SLOT}[pos]
APEX_H = 64                     # roof / vee top stars sit this far off the line (key sheet)
APEX_H_RANGE = (48, 150)        # ... or a random height
SMALL_GAP = 30                  # lines stop this far from a small star's center (same visible gap as LINE_GAP)
MIN_STROKE = 25                 # shortest roof / vee stroke from a big star
MIN_RISE = math.tan(math.radians(14))  # roof strokes leave the big star at least this steeply, so they clear the main line
TOP_CLEAR = LINE_GAP + SMALL_GAP + MIN_STROKE  # top stars keep at least this far (along the line) from both big stars
TOP_APART = 2 * SMALL_GAP + 12  # neighboring top stars keep at least this far apart along the line
ZIG_DEPTH = 16                  # roof3 / vee3: the middle top star sits this much lower than the outer two
KEY_STEP = 80                   # key sheet: distance between neighboring top stars
APEX_SPLIT = 40                 # small stars closer than this to the line are slot stars, farther are apex stars
DOUBLE_GAP = 6                  # each line of a double line sits this far off the center
LABEL_GAP = 40                  # word numbers sit this far behind the first star's center (plus half their size)
LABEL_SIZE = 42
LABEL_FONT = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"  # serif, so "I" never looks like a stroke
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

MAX_TURN = math.radians(110)    # max turn from one letter's line to the next
MARGIN = 110
CLEAR = 22                      # min gap between drawn parts of different letters
STAR_CLEAR = 100                # min gap between a big star / label and other letters' drawing
NODE_GAP = 200                  # min distance between big stars
OWN_MARGIN = 18                 # a small star must be this much closer to its own line than to any other


def _check_slot_room():
    """On the shortest line, every slot star must sit nearer its own slot position than any other,
    which is how the decoder sorts them."""
    L = EDGE_RANGE[0]
    for ch, code in ab.CODES.items():
        for slot in ab.SLOTS:
            n = code.get(slot, 0)
            for edge in (-1, 1):
                x = slot_center(slot[0], L) + edge * (n - 1) / 2 * SPACING
                own = abs(x - slot_center(slot[0], L))
                other = min(abs(x - slot_center(q, L)) for q in "SME" if q != slot[0])
                assert n == 0 or other - own >= 6, f"{ch}: {slot} stars crowd another slot on a {L} px line"


_check_slot_room()


def font(size, path=FONT):
    return ImageFont.truetype(path, int(size * SS))


ROMAN = [(100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def roman(n):
    """Roman numeral for n >= 1."""
    out = ""
    for value, sym in ROMAN:
        while n >= value:
            out, n = out + sym, n - value
    return out


def unroman(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    return sum(-vals[a] if vals[a] < vals[b] else vals[a] for a, b in zip(s, s[1:] + "I")) if s else None


LABEL_LETTER_GAP = 5            # px between the letters of a word number, so serifs never touch


def label_layout(s):
    """Center x offset of each letter of a word number, and the total width / height (final px)."""
    f = font(LABEL_SIZE, LABEL_FONT)
    widths = [(f.getbbox(ch)[2] - f.getbbox(ch)[0]) / SS for ch in s]
    total = sum(widths) + LABEL_LETTER_GAP * (len(s) - 1)
    xs, x = [], -total / 2
    for w in widths:
        xs.append(x + w / 2)
        x += w + LABEL_LETTER_GAP
    height = (f.getbbox(s)[3] - f.getbbox(s)[1]) / SS
    return xs, total, height


def label_size(s):
    """Width, height of a rendered word number, in final pixels."""
    _, w, h = label_layout(s)
    return w, h


def min_edge(ch):
    """Shortest line that has room for this letter's roof / vee top stars."""
    n = max(ab.CODES[ch].get("roof", 0), ab.CODES[ch].get("vee", 0))
    return max(EDGE_RANGE[0], 2 * TOP_CLEAR + (n - 1) * TOP_APART + 20) if n else EDGE_RANGE[0]


def star_outline(cx, cy, rx, ry, steps=12):
    """Four-point sparkle: tips joined by inward-bending curves."""
    tips = [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]
    pts = []
    for i in range(4):
        (x0, y0), (x2, y2) = tips[i], tips[(i + 1) % 4]
        x1, y1 = cx + (x0 + x2 - 2 * cx) * 0.08, cy + (y0 + y2 - 2 * cy) * 0.08
        for k in range(steps):
            t = k / steps
            pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2,
                        (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2))
    return pts


FONT_FAMILY = {FONT: "Arial Unicode MS, Arial, sans-serif", LABEL_FONT: "Times New Roman, Times, serif"}


def rgb(c):
    return "#%02x%02x%02x" % c


def star_svg_path(cx, cy, rx, ry):
    """The same four-point sparkle as star_outline, as exact SVG curves."""
    tips = [(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)]
    d = f"M{tips[0][0]:.2f},{tips[0][1]:.2f}"
    for i in range(4):
        (x0, y0), (x2, y2) = tips[i], tips[(i + 1) % 4]
        x1, y1 = cx + (x0 + x2 - 2 * cx) * 0.08, cy + (y0 + y2 - 2 * cy) * 0.08
        d += f" Q{x1:.2f},{y1:.2f} {x2:.2f},{y2:.2f}"
    return d + " Z"


class Sheet:
    """Draws into a supersampled raster (for JPGs and for trimming) and records every
    shape so the same picture can be written as an SVG."""

    def __init__(self, w, h):
        self.w, self.h = int(w), int(h)
        self.img = Image.new("RGB", (self.w * SS, self.h * SS), PAPER)
        self.d = ImageDraw.Draw(self.img)
        self.svg = []

    def star(self, p, big, solid=False):
        """A four-point star; `solid` fills it in (the end star of a digit)."""
        rx, ry, w = (BIG_RX, BIG_RY, 3) if big else (SMALL_RX, SMALL_RY, 2.5)
        pts = star_outline(p[0] * SS, p[1] * SS, rx * SS, ry * SS)
        if solid:
            self.d.polygon(pts, fill=INK)
        self.d.line(pts + [pts[0]], fill=INK, width=round(w * SS), joint="curve")
        fill = f' fill="{rgb(INK)}"' if solid else ""
        self.svg.append(f'<path d="{star_svg_path(p[0], p[1], rx, ry)}" stroke-width="{w}"{fill}/>')

    def line(self, a, b, width=LINE_W):
        self.d.line([(a[0] * SS, a[1] * SS), (b[0] * SS, b[1] * SS)], fill=INK, width=round(width * SS))
        self.svg.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" stroke-width="{width}"/>')

    def text(self, p, s, size, fill=INK, path=FONT):
        self.d.text((p[0] * SS, p[1] * SS), s, font=font(size, path), fill=fill, anchor="mm")
        # PIL's "mm" anchor puts the middle of ascender..descender at p; SVG gets the matching baseline
        ascent, descent = font(size, path).getmetrics()
        base = p[1] + (ascent - descent) / 2 / SS
        self.svg.append(f'<text x="{p[0]:.2f}" y="{base:.2f}" font-family="{FONT_FAMILY[path]}" font-size="{size}" '
                        f'fill="{rgb(fill)}" stroke="none" text-anchor="middle">{s}</text>')

    def label(self, p, s):
        """A word number, letter by letter with a fixed gap (same in the JPG and the SVG)."""
        xs, _, _ = label_layout(s)
        for ch, dx in zip(s, xs):
            self.text((p[0] + dx, p[1]), ch, LABEL_SIZE, path=LABEL_FONT)

    def save(self, path, pad=None):
        """Write a JPG, or an SVG when `path` ends in .svg.
        With `pad`, trim the empty sky to `pad` px around the drawing."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        img = self.img.resize((self.w, self.h), Image.LANCZOS)
        paper = Image.new("RGB", (1, 1), PAPER).convert("L").getpixel((0, 0))
        box = img.convert("L").point(lambda v: 255 if abs(v - paper) > 55 else 0).getbbox() if pad is not None else None
        x0, y0, x1, y1 = 0, 0, self.w, self.h
        if box:
            x0, y0 = max(box[0] - pad, 0), max(box[1] - pad, 0)
            x1, y1 = min(box[2] + pad, self.w), min(box[3] + pad, self.h)
        if str(path).lower().endswith(".svg"):
            w, h = x1 - x0, y1 - y0
            Path(path).write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{x0} {y0} {w} {h}">\n'
                f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="{rgb(PAPER)}"/>\n'
                f'<g fill="none" stroke="{rgb(INK)}" stroke-linejoin="round">\n'
                + "\n".join(self.svg) + "\n</g>\n</svg>\n")
        else:
            img.crop((x0, y0, x1, y1)).save(path, quality=92)


def label_image(s):
    """The word-index label exactly as it is rendered (grayscale, final scale); used by the decoder."""
    sheet = Sheet(LABEL_SIZE * len(s) + 40, LABEL_SIZE + 40)
    sheet.label((sheet.w / 2, sheet.h / 2), s)
    return sheet.img.resize((sheet.w, sheet.h), Image.LANCZOS).convert("L")


def frame(a, b):
    """Map (along, above) letter coordinates on line a -> b to image coordinates.
    `above` is measured to the left of travel (image y points down)."""
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    return L, lambda t, h: (a[0] + ux * t + uy * h, a[1] + uy * t - ux * h)


def point_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def between(p, q, g0, g1):
    """Stroke from p toward q (letter coordinates), stopping g0 short of p and g1 short of q."""
    d = math.dist(p, q)
    ut, uh = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    return (p[0] + ut * g0, p[1] + uh * g0), (q[0] - ut * g1, q[1] - uh * g1)


def key_edge(ch):
    """Line length for this symbol on the key sheet (long chains need more room)."""
    n = max(ab.CODES[ch].get("roof", 0), ab.CODES[ch].get("vee", 0))
    return max(EDGE, (n - 1) * KEY_STEP + 220)


def _peak_try(L, n, side, rng, guard):
    """One random roof / vee in letter coordinates: (strokes, top stars), or None if it doesn't fit.
    Top stars sit at random distances along the line; every gap at a star is fixed."""
    pick = rng.uniform
    lo, hi = TOP_CLEAR, L - TOP_CLEAR
    span = hi - lo - (n - 1) * TOP_APART
    if span < 0:
        return None
    # random spots with at least TOP_APART between neighbors
    ts = [lo + x + i * TOP_APART for i, x in enumerate(sorted(pick(0, span) for _ in range(n)))]
    # the outer top stars must sit high enough for their strokes to rise steeply from the big stars
    need = (MIN_RISE * ts[0], MIN_RISE * (L - ts[-1]))
    top = APEX_H_RANGE[1]
    if n == 3:
        h_lo = max(APEX_H_RANGE[0] + ZIG_DEPTH, *need)
        if h_lo > top:
            return None
        H = pick(h_lo, top)
        hs = [H, H - ZIG_DEPTH, H]
    elif n == 2:  # each top star gets its own height
        if max(need) > top:
            return None
        hs = [pick(max(APEX_H_RANGE[0], need[0]), top), pick(max(APEX_H_RANGE[0], need[1]), top)]
    else:
        h_lo = max(APEX_H_RANGE[0], *need)
        if h_lo > top:
            return None
        hs = [pick(h_lo, top)]
    stars = [(t, h * side) for t, h in zip(ts, hs)]
    thin = [between(s0, s1, SMALL_GAP, SMALL_GAP) for s0, s1 in zip(stars, stars[1:])]  # dash / zigzag pieces
    thick = [between((0, 0), stars[0], LINE_GAP, SMALL_GAP), between((L, 0), stars[-1], LINE_GAP, SMALL_GAP)]
    for g in guard:  # middle-slot stars on this side must stay clear of the whole peak
        if any(point_seg(g, p, q) < 20 for p, q in thick + thin) or any(math.dist(g, t) < 30 for t in stars):
            return None
    return thick, thin, stars


def peak_shape(at, L, n, side, rng, lines, smalls, guard):
    """Roof (side=+1) or vee (side=-1): n small stars at the top, joined to the two big stars
    by strokes pointing straight from each big star to its nearest top star.
    With `rng`, the top stars sit at random distances and heights between the big stars;
    without it, the fixed key-sheet shape is drawn.
    `guard`: slot-star positions on this side the peak must keep clear of."""
    if rng is None:
        H, mid = APEX_H, L / 2
        ts = [mid + (i - (n - 1) / 2) * KEY_STEP for i in range(n)]
        hs = {1: [H], 2: [H, H], 3: [H, H - ZIG_DEPTH, H]}[n]
        stars = [(t, h * side) for t, h in zip(ts, hs)]
        thin = [between(s0, s1, SMALL_GAP, SMALL_GAP) for s0, s1 in zip(stars, stars[1:])]
        thick = [between((0, 0), stars[0], LINE_GAP, SMALL_GAP), between((L, 0), stars[-1], LINE_GAP, SMALL_GAP)]
    else:
        for _ in range(400):
            res = _peak_try(L, n, side, rng, guard)
            if res:
                break
        else:
            raise RuntimeError(f"no room for a roof/vee on a {L:.0f} px line")
        thick, thin, stars = res
    lines += [(at(*p), at(*q), LINE_W) for p, q in thick] + [(at(*p), at(*q), THIN_W) for p, q in thin]
    smalls += [(at(t, h), abs(h)) for t, h in stars]


def slot_points(code, L):
    """Letter coordinates of every slot star: {slot: [(along, above), ...]}."""
    out = {}
    for slot in ab.SLOTS:
        n = code.get(slot, 0)
        side = 1 if slot[1] == "a" else -1
        out[slot] = [(slot_center(slot[0], L) + (i - (n - 1) / 2) * SPACING, OFFSET * side) for i in range(n)]
    return out


def letter_shape(a, b, ch, rng=None):
    """Everything one letter draws on line a -> b: {'lines': [(p, q, width)], 'smalls': [(p, off)]},
    where `off` is how far the small star sits from its own line."""
    code = ab.CODES[ch]
    L, at = frame(a, b)
    lines, smalls = [], []
    for h in ((-DOUBLE_GAP, DOUBLE_GAP) if code.get("double") else (0,)):
        lines.append((at(LINE_GAP, h), at(L - LINE_GAP, h), LINE_W))
    if code.get("cross"):
        dt, dh = 15 * math.cos(math.radians(60)), 15 * math.sin(math.radians(60))
        for t in (L / 2 - 6, L / 2 + 6):
            lines.append((at(t - dt, -dh), at(t + dt, dh), LINE_W))
    slots = slot_points(code, L)
    for form, side in (("roof", 1), ("vee", -1)):
        if code.get(form):
            guard = [p for slot, pts in slots.items() if (slot[1] == "a") == (side == 1) for p in pts]
            peak_shape(at, L, code[form], side, rng, lines, smalls, guard)
    smalls += [(at(*p), abs(p[1])) for pts in slots.values() for p in pts]
    shape = {"lines": lines, "smalls": smalls, "solid_end": bool(code.get("solid"))}  # digits end in a solid star
    shape["samples"] = sample_shape(shape)
    return shape


def draw_shape(sheet, shape):
    for p, q, width in shape["lines"]:
        sheet.line(p, q, width)
    for p, _ in shape["smalls"]:
        sheet.star(p, big=False)


def draw_letter(sheet, a, b, ch, rng=None):
    draw_shape(sheet, letter_shape(a, b, ch, rng))


# ---------- layout ----------

def sample_shape(shape):
    """Points along every stroke (every 8 px) plus every small star center."""
    pts = []
    for p, q, _ in shape["lines"]:
        n = max(2, int(math.dist(p, q) / 8) + 1)
        pts += [(p[0] + (q[0] - p[0]) * i / (n - 1), p[1] + (q[1] - p[1]) * i / (n - 1)) for i in range(n)]
    pts += [p for p, _ in shape["smalls"]]
    return np.array(pts)


def closer_to(p, off, a, b):
    """Would the decoder give small star p (off px from its own line) to line a-b instead?"""
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    vx, vy = p[0] - a[0], p[1] - a[1]
    t = (vx * ux + vy * uy) / L
    return -0.1 < t < 1.1 and abs(vx * uy - vy * ux) < off + OWN_MARGIN


class World:
    """Everything placed so far, with undo for backtracking."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.parts, self.blobs, self.edges, self.smalls = [], [], [], []
        self.version, self._tree = 0, (None, None)

    def mark(self):
        return len(self.parts), len(self.blobs), len(self.edges), len(self.smalls)

    def undo(self, m):
        del self.parts[m[0]:], self.blobs[m[1]:], self.edges[m[2]:], self.smalls[m[3]:]
        self.version += 1

    def tree(self):
        """Spatial index of every drawn point, rebuilt only after the drawing changes."""
        if self._tree[0] != self.version:
            self._tree = (self.version, cKDTree(np.concatenate(self.parts)) if self.parts else None)
        return self._tree[1]

    def nearest(self, pts):
        """Distance from each point to the closest drawn point (inf when nothing is drawn yet)."""
        t = self.tree()
        return t.query(pts)[0] if t is not None else np.full(len(np.atleast_2d(pts)), np.inf)

    def inside(self, p, m=MARGIN):
        return m <= p[0] <= self.w - m and m <= p[1] <= self.h - m

    def free_spot(self, p, skip=None, clear=STAR_CLEAR):
        """Room for a big star or a label at p."""
        return (all(math.dist(p, q) >= NODE_GAP for q in self.blobs if q is not skip)
                and np.min(self.nearest([p])) >= clear)

    def letter_fits(self, cur, nxt, shape):
        S = shape["samples"]
        if S.min() < 30 or S[:, 0].max() > self.w - 30 or S[:, 1].max() > self.h - 30:
            return False  # a tall roof / vee would stick out of the picture
        if np.min(self.nearest(S)) < CLEAR:
            return False
        others = [q for q in self.blobs if q is not cur]
        if others and cKDTree(S).query(others)[0].min() < STAR_CLEAR:
            return False
        if any(closer_to(p, off, a, b) for p, off in shape["smalls"] for a, b in self.edges):
            return False
        return not any(closer_to(p, off, cur, nxt) for p, off in self.smalls)

    def add_letter(self, cur, nxt, shape):
        self.version += 1
        self.parts.append(shape["samples"])
        self.edges.append((cur, nxt))
        self.smalls += shape["smalls"]
        self.blobs.append(nxt)


def _place_word(word, index, world, rng):
    """Random chain of big stars for one word; returns (nodes, shapes, label_pos) or None."""
    budget = [400]

    def grow(nodes, shapes, heading):
        if len(shapes) == len(word):
            return True
        budget[0] -= 1
        if budget[0] < 0:
            return False
        cur = nodes[-1]
        for _ in range(10):
            ang = rng.uniform(0, 2 * math.pi) if heading is None else heading + rng.uniform(-MAX_TURN, MAX_TURN)
            L = rng.uniform(min_edge(word[len(shapes)]), EDGE_RANGE[1])
            nxt = (cur[0] + L * math.cos(ang), cur[1] + L * math.sin(ang))
            if not (world.inside(nxt) and world.free_spot(nxt, skip=cur)):
                continue
            shape = letter_shape(cur, nxt, word[len(shapes)], rng)
            if not world.letter_fits(cur, nxt, shape):
                continue
            m = world.mark()
            if heading is None:  # first letter: the number label sits behind the start star
                lw, lh = label_size(roman(index + 1))
                dist = LABEL_GAP + abs(math.cos(ang)) * lw / 2 + abs(math.sin(ang)) * lh / 2
                lab = (cur[0] - dist * math.cos(ang), cur[1] - dist * math.sin(ang))
                room = max(lw, lh) / 2
                if not (world.inside(lab, 30 + room) and world.free_spot(lab, skip=cur, clear=35 + room)
                        and np.min(np.hypot(*(shape["samples"] - lab).T)) >= 30 + room):
                    continue
                world.blobs.append(lab)
            world.add_letter(cur, nxt, shape)
            nodes.append(nxt)
            shapes.append(shape)
            if grow(nodes, shapes, ang):
                return True
            nodes.pop()
            shapes.pop()
            world.undo(m)
        return False

    for _ in range(200):
        start = (rng.uniform(MARGIN, world.w - MARGIN), rng.uniform(MARGIN, world.h - MARGIN))
        if not (world.free_spot(start)):
            continue
        m = world.mark()
        world.blobs.append(start)
        nodes, shapes = [start], []
        if grow(nodes, shapes, None):
            return nodes, shapes, world.blobs[m[1] + 1]
        world.undo(m)
        budget[0] = 400
    return None


def footprint(ch):
    """Rough area one letter needs: its average line length times the band its stars reach."""
    code = ab.CODES[ch]
    reach = APEX_H_RANGE[1] if (code.get("roof") or code.get("vee")) else 60
    return (min_edge(ch) + EDGE_RANGE[1]) / 2 * (2 * reach + 160)


class Progress:
    """A one-line progress bar on stderr: [#########-----------]  45%  placing word 9/20"""

    def __init__(self, enabled, width=30):
        self.enabled, self.width, self.last = enabled, width, ""

    def show(self, frac, note):
        if not self.enabled:
            return
        filled = int(self.width * max(0.0, min(1.0, frac)))
        line = f"\r[{'#' * filled}{'-' * (self.width - filled)}] {frac * 100:3.0f}%  {note}"
        sys.stderr.write(line + " " * max(0, len(self.last) - len(line)))  # wipe leftovers of a longer line
        sys.stderr.flush()
        self.last = line

    def finish(self):
        if self.enabled:
            sys.stderr.write("\r" + " " * len(self.last) + "\r")
            sys.stderr.flush()


PLACE_SHARE = 0.85  # share of the bar for placing words; drawing and saving get the rest


def layout(words, rng, progress=None):
    progress = progress or Progress(False)
    area = sum(sum(footprint(ch) for ch in wd) + EDGE_RANGE[1] ** 2 / 2 for wd in words) * 1.5
    w = max(800.0, math.sqrt(area * 4 / 3))
    h = max(600.0, w * 3 / 4)
    attempt = 0
    for _ in range(40):
        for _ in range(20):
            attempt += 1
            world, placed = World(w, h), []
            for index, word in enumerate(words):
                retry = f", attempt {attempt}" if attempt > 1 else ""
                progress.show(PLACE_SHARE * index / len(words), f"placing word {index + 1}/{len(words)}{retry}")
                res = _place_word(word, index, world, rng)
                if res is None:
                    break
                placed.append(res)
            else:
                return w, h, placed
        w, h = w * 1.12, h * 1.12
    raise RuntimeError("could not lay out the constellation")


def encode(text, out, seed=None, progress=False):
    """Encode text into a picture at `out`. `progress=True` shows a progress bar on stderr."""
    words, dropped = ab.tokenize(text)
    if dropped:
        print(f"treated as spaces (no cipher symbol): {''.join(sorted(dropped))}", file=sys.stderr)
    if not words:
        raise SystemExit("nothing to encode")
    bar = Progress(progress)
    rng = random.Random(seed)
    w, h, placed = layout(words, rng, bar)
    sheet = Sheet(w, h)
    for idx, (nodes, shapes, label) in enumerate(placed):
        bar.show(PLACE_SHARE + 0.1 * idx / len(placed), f"drawing word {idx + 1}/{len(placed)}")
        for shape in shapes:
            draw_shape(sheet, shape)
        solid = [False] + [shape["solid_end"] for shape in shapes]
        for p, is_solid in zip(nodes, solid):
            sheet.star(p, big=True, solid=is_solid)
        sheet.label(label, roman(idx + 1))
    bar.show(0.95, "saving")
    sheet.save(out, pad=70)
    bar.show(1.0, "done")
    bar.finish()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text")
    ap.add_argument("-o", "--out", default="out/message.jpg", help="output .jpg (default) or .svg")
    ap.add_argument("--seed", type=int, help="same seed + same text = same picture")
    args = ap.parse_args()
    print(encode(args.text, args.out, args.seed))


if __name__ == "__main__":
    main()
