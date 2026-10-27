"""Decode an astro cipher JPG (made by encode.py) back into text.

    python decode.py out/tonight.svg [-v]     (SVG, JPG or PNG)

Reads the picture itself: finds big stars, small stars, lines and the Roman word numbers,
walks each word from the star its number sits next to, and reads every line's slots
and forms (roof / vee top stars, double line, "//" cross mark, hollow end star = digit).
"""
import argparse
import io
import math

import numpy as np
from PIL import Image
from scipy import ndimage

import alphabet as ab
import encode as en

INK_DIFF = 90  # a pixel is ink when it differs this much from the background (works light-on-dark or dark-on-light)


def ink(gray):
    bg = np.median(gray)  # the sky / paper covers most of the picture
    return np.abs(gray.astype(int) - bg) > INK_DIFF


def components(gray):
    lab, _ = ndimage.label(ink(gray), structure=np.ones((3, 3)))
    comps = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        mask = lab[sl] == i
        ys, xs = np.nonzero(mask)
        if len(xs) < 6:
            continue
        ys, xs = ys + sl[0].start, xs + sl[1].start
        h, w = mask.shape
        c = dict(mask=mask, x0=sl[1].start, y0=sl[0].start, w=w, h=h,
                 cx=sl[1].start + (w - 1) / 2, cy=sl[0].start + (h - 1) / 2)
        pts = np.stack([xs, ys], 1).astype(float)
        mean = pts.mean(0)
        evals, evecs = np.linalg.eigh(np.cov((pts - mean).T))
        axis = evecs[:, 1]
        proj = (pts - mean) @ axis
        c["extent"] = proj.max() - proj.min()
        c["thin"] = math.sqrt(max(evals[0], 0))
        c["ends"] = (tuple(pts[proj.argmin()]), tuple(pts[proj.argmax()]))
        size = max(w, h)
        if c["extent"] > 100 and len(xs) / c["extent"] < 9:
            c["kind"] = "line"
            # a "//" mark sticks out of the line's axis
            c["cross"] = int((np.abs((pts - mean) @ evecs[:, 0]) > 6).sum() > 25)
        elif c["thin"] < 2:
            c["kind"] = "other"  # roof / vee strokes, dashes, digit "1"
        elif 38 <= size < 60 and c["thin"] > 4:
            c["kind"] = "big"
        elif 10 <= size <= 25:
            c["kind"] = "small"
        else:
            c["kind"] = "other"  # label digits, long strokes
        comps.append(c)
    return comps


_TEMPLATES = None


def _templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        _TEMPLATES = {}
        for d in "IVXLC":
            g = ink(np.asarray(en.label_image(d)))
            ys, xs = np.nonzero(g)
            crop = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            _TEMPLATES[d] = (_norm(crop), crop.shape)
    return _TEMPLATES


def _norm(mask):
    return np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).resize((24, 34), Image.BILINEAR)) > 127


def as_numeral(c):
    """The Roman numeral letter this mark is, or None when it doesn't really look like one (e.g. a short stroke)."""
    m = _norm(c["mask"])
    best, score = None, 0.0
    for d, (t, (th, tw)) in _templates().items():
        if abs(c["h"] - th) > 4 or abs(c["w"] - tw) > max(4, 0.25 * tw):
            continue
        iou = (m & t).sum() / max((m | t).sum(), 1)
        if iou > score:
            best, score = d, iou
    return best if score >= 0.6 else None


def read_label(comps):
    return en.unroman("".join(c["numeral"] for c in sorted(comps, key=lambda c: c["cx"])))


def axis_dist(p, a, b):
    """Distance from p to the infinite line through a and b."""
    L = math.dist(a, b)
    return abs((p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])) / L


def load_gray(path):
    """Grayscale pixels of a JPG/PNG, or of an SVG rendered at its own size."""
    if str(path).lower().endswith(".svg"):
        import resvg_py
        png = resvg_py.svg_to_bytes(svg_path=str(path))
        return np.asarray(Image.open(io.BytesIO(bytes(png))).convert("L"))
    return np.asarray(Image.open(path).convert("L"))


def decode(path, verbose=False):
    gray = load_gray(path)
    comps = components(gray)
    by = {k: [c for c in comps if c["kind"] == k] for k in ("line", "big", "small", "other")}
    stars = [(c["cx"], c["cy"]) for c in by["big"]]
    # every star is filled except a digit's end star: its center is empty sky
    hollow = [c["mask"][c["h"] // 2 - 2:c["h"] // 2 + 3, c["w"] // 2 - 2:c["w"] // 2 + 3].mean() < 0.5 for c in by["big"]]

    def nearest_star(p, limit):
        if not stars:
            return None
        i = min(range(len(stars)), key=lambda i: math.dist(p, stars[i]))
        return i if math.dist(p, stars[i]) <= limit else None

    adj = {i: set() for i in range(len(stars))}
    lines_on = {}  # (a, b) with a < b -> line components drawn between those stars
    for ln in by["line"]:
        a, b = (nearest_star(e, en.LINE_GAP + 30) for e in ln["ends"])
        # a letter line lies on the axis between its two stars; roof strokes and dashes don't
        if a is not None and b is not None and a != b and all(
                axis_dist(e, stars[a], stars[b]) <= en.DOUBLE_GAP + 8 for e in ln["ends"]):
            adj[a].add(b)
            adj[b].add(a)
            lines_on.setdefault((min(a, b), max(a, b)), []).append(ln)

    # each small star belongs to the closest line it sits beside
    beside = {}
    for s in by["small"]:
        p, best = (s["cx"], s["cy"]), None
        for a in adj:
            for b in adj[a]:
                if a > b:
                    continue
                A, B = stars[a], stars[b]
                L = math.dist(A, B)
                ux, uy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
                t = ((p[0] - A[0]) * ux + (p[1] - A[1]) * uy) / L
                perp = abs((p[0] - A[0]) * uy - (p[1] - A[1]) * ux)
                if -0.05 < t < 1.05 and perp < en.APEX_H_RANGE[1] + 22 and (best is None or perp < best[0]):
                    best = (perp, (a, b))
        if best:
            beside.setdefault(best[1], []).append(p)

    def read_edge(a, b):
        A, B = stars[a], stars[b]
        L = math.dist(A, B)
        ux, uy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
        counts = {}
        edge = (min(a, b), max(a, b))
        near = {"a": [], "b": []}  # slot stars: distance along the line, per side
        for p in beside.get(edge, []):
            vx, vy = p[0] - A[0], p[1] - A[1]
            off = uy * vx - ux * vy  # distance on the "above" side (left of travel)
            if abs(off) > en.APEX_SPLIT:
                name = "roof" if off > 0 else "vee"
                counts[name] = counts.get(name, 0) + 1
            else:
                near["a" if off > 0 else "b"].append(vx * ux + vy * uy)
        for side, along in near.items():
            for s in along:  # each slot star belongs to the nearest slot position
                pos = min("SME", key=lambda q: abs(en.slot_center(q, L) - s))
                counts[pos + side] = counts.get(pos + side, 0) + 1
        lines = lines_on.get(edge, [])
        if len(lines) > 1:
            counts["double"] = 1
        if any(ln["cross"] for ln in lines):
            counts["cross"] = 1
        if hollow[b]:  # the star we walk *to* is hollow: this line is a digit
            counts["hollow"] = 1
        return counts

    # word numbers: Roman-numeral marks, grouped left to right on one baseline
    labels = []
    marks = [c for c in by["other"] if 20 <= max(c["w"], c["h"]) <= 40]
    for c in marks:
        c["numeral"] = as_numeral(c)
    for c in sorted((c for c in marks if c["numeral"]), key=lambda c: c["cx"]):
        group = next((g for g in labels if abs(c["cy"] - g[-1]["cy"]) < 12 and 0 < c["cx"] - g[-1]["cx"] < 50), None)
        if group:
            group.append(c)
        else:
            labels.append([c])

    words = []
    for group in labels:
        lc = (sum(c["cx"] for c in group) / len(group), sum(c["cy"] for c in group) / len(group))
        start = nearest_star(lc, en.NODE_GAP - 30)
        if start is None or not adj[start]:
            continue
        label = read_label(group)
        path, prev = [start], None
        while True:
            nxt = [j for j in adj[path[-1]] if j != prev and j not in path]
            if not nxt:
                break
            prev = path[-1]
            path.append(nxt[0])
        codes = [read_edge(a, b) for a, b in zip(path, path[1:])]
        words.append((label, codes))
    words.sort(key=lambda w: (w[0] is None, w[0]))

    # look-alike letters (А/A ...) take the script of the word's other letters, else of the sentence
    decoded = []
    for _, codes in words:
        decoded.append([ab.DECODE.get(ab.key(c), ["?"]) for c in codes])
    tally = {"ru": 0, "en": 0}
    for word in decoded:
        for opts in word:
            if len(opts) == 1 and ab.SCRIPT.get(opts[0]) in tally:
                tally[ab.SCRIPT[opts[0]]] += 1
    sentence_script = "en" if tally["en"] > tally["ru"] else "ru"
    out = []
    for word in decoded:
        scripts = {ab.SCRIPT[o[0]] for o in word if len(o) == 1 and ab.SCRIPT.get(o[0]) in tally}
        script = scripts.pop() if len(scripts) == 1 else sentence_script
        out.append("".join(o[0] if len(o) == 1 else next(c for c in o if ab.SCRIPT[c] == script) for o in word))

    if verbose:
        for (label, codes), text in zip(words, out):
            print(f"word {label}: {text}  <- " + " | ".join(ab.fmt(c) or "plain" for c in codes))
    return " ".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("-v", "--verbose", action="store_true", help="show the slot code read for every letter")
    args = ap.parse_args()
    print(decode(args.image, args.verbose))


if __name__ == "__main__":
    main()
