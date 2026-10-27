"""Encode sample sentences to JPG, decode them back, and check the text survives.

    python test_roundtrip.py
"""
import tempfile
from pathlib import Path

import alphabet as ab
import decode
import encode

SAMPLES = [
    "Лагерь Маши",
    "Я люблю тебя",
    "the quick brown fox jumps over the lazy dog",
    "съешь же ещё этих мягких французских булок",
    "0123456789 42",
    "ТОР",           # only look-alike letters -> falls back to Russian
    "Hello Мир",
    " ".join(ab.RU),  # every Russian letter as its own word
]


def expected(text):
    words, _ = ab.tokenize(text)
    return " ".join("".join(w) for w in words)


def main():
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for i, text in enumerate(SAMPLES):
            for seed, ext in ((1, "svg"), (2, "jpg")):  # both output formats
                path = Path(tmp) / f"{i}_{seed}.{ext}"
                encode.encode(text, path, seed=seed)
                got, want = decode.decode(path), expected(text)
                ok = got == want
                failed += not ok
                print(f"{'ok  ' if ok else 'FAIL'} {ext} {want!r}" + ("" if ok else f" -> {got!r}"))
    print("all passed" if not failed else f"{failed} failed")
    raise SystemExit(failed > 0)


if __name__ == "__main__":
    main()
