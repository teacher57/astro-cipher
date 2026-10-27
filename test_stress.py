"""Encode sentences with many random layouts (half SVG, half JPG), decode them, check the text
survives, and report the time per encode + decode. Pictures go to a temp folder.

    python test_stress.py [layouts per sentence, default 12]
"""
import sys
import tempfile
import time
from pathlib import Path

import decode
import encode
from test_roundtrip import expected

SENTENCES = [
    "the quick brown fox jumps over the lazy dog",
    "съешь же ещё этих мягких французских булок",
    "Шла Саша по шоссе и сосала сушку",
    "0123456789 42 1990 2026",
    "call me at 8-905-123-45-67",
    "R2D2 and C3PO 4ever",
    "П1 Ш2 Ь3 К4 U5 S6 Ж7 О0",  # digits next to the letters whose shapes they share
    "Ьь Щ Ъ Ф Ж Й suzu wuv",
    "a b c d e f g h i j k l m n o p q r s t u v w x y z",
]


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    fails = n = 0
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        for text in SENTENCES:
            for seed in range(per):
                path = Path(tmp) / f"stress.{'svg' if seed % 2 == 0 else 'jpg'}"
                encode.encode(text, path, seed=1000 + seed)
                got = decode.decode(path)
                n += 1
                if got != expected(text):
                    fails += 1
                    print(f"FAIL {path.suffix} seed {1000 + seed}: {expected(text)!r} -> {got!r}")
    print(f"{n} layouts, {fails} failed, {(time.time() - t0) / n:.1f}s per encode + decode")
    raise SystemExit(fails > 0)


if __name__ == "__main__":
    main()
