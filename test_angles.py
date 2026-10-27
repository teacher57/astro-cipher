"""Draw every symbol alone at 24 line angles with random lengths and shapes, decode it, and check
it comes back (look-alikes such as А / A count as the same picture). Pictures go to a temp folder.

    python test_angles.py
"""
import math
import random
import tempfile
from pathlib import Path

import alphabet as ab
import decode
import encode as en


def main():
    rng = random.Random(11)
    bad, n = [], 0
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "symbol.jpg"
        seen = set()
        for ch, code in ab.CODES.items():
            key = ab.key(code)
            if key in seen:  # look-alikes share one picture: test it once
                continue
            seen.add(key)
            for deg in range(0, 360, 15):
                r = math.radians(deg)
                L = rng.uniform(en.min_edge(ch), en.EDGE_RANGE[1])
                c = (650, 650)
                a = (c[0] - L / 2 * math.cos(r), c[1] - L / 2 * math.sin(r))
                b = (c[0] + L / 2 * math.cos(r), c[1] + L / 2 * math.sin(r))
                sheet = en.Sheet(1300, 1300)
                en.draw_letter(sheet, a, b, ch, rng)
                sheet.star(a, big=True)
                sheet.star(b, big=True, solid=bool(code.get("solid")))
                lw, lh = en.label_size("I")
                d = en.LABEL_GAP + abs(math.cos(r)) * lw / 2 + abs(math.sin(r)) * lh / 2
                sheet.label((a[0] - d * math.cos(r), a[1] - d * math.sin(r)), "I")
                sheet.save(path)
                got = decode.decode(path)
                n += 1
                if got not in ab.CODES or ab.key(ab.CODES[got]) != key:
                    bad.append((ch, deg, round(L), got))
    print(f"{n} symbol / angle / length checks, {len(bad)} failed")
    for b in bad[:20]:
        print("FAIL", b)
    raise SystemExit(bool(bad))


if __name__ == "__main__":
    main()
