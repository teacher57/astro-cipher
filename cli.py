"""astrocipher: hide text in a constellation picture, and read it back.

    astrocipher encode "i invented a cipher"         -> writes <sha256 of the picture>.jpg here
    astrocipher encode "Лагерь Маши" --svg            -> <sha256>.svg (vector image)
    astrocipher encode "Лагерь Маши" -o pics/         -> <sha256>.jpg inside pics/
    astrocipher encode "Лагерь Маши" -o lager.jpg     -> exactly that name (.jpg or .svg)
    astrocipher decode 3f9a...c1.jpg [-v]             (JPG, SVG or PNG)
    astrocipher alphabet                              -> re-renders alphabet/ and RULES.md
"""
import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import decode  # noqa: E402
import encode  # noqa: E402


def encode_to(text, out=None, svg=False, seed=None, progress=False):
    """Encode `text`. When `out` is a file name, write exactly there; when it is a folder (or not given),
    name the file by the SHA-256 of the picture, so the name says nothing about the message."""
    if out and Path(out).suffix.lower() in (".jpg", ".jpeg", ".svg", ".png"):
        return encode.encode(text, out, seed, progress)
    folder = Path(out or ".")
    folder.mkdir(parents=True, exist_ok=True)
    ext = ".svg" if svg else ".jpg"
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        tmp_path = Path(tmp) / f"picture{ext}"
        encode.encode(text, tmp_path, seed, progress)
        final = folder / f"{hashlib.sha256(tmp_path.read_bytes()).hexdigest()}{ext}"
        tmp_path.replace(final)
    return final


def main():
    ap = argparse.ArgumentParser(prog="astrocipher", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode", help="turn text into a constellation picture named by its SHA-256")
    enc.add_argument("text")
    enc.add_argument("-o", "--out", help="output folder (file named by SHA-256) or an exact .jpg / .svg file name")
    enc.add_argument("--svg", action="store_true", help="save a vector .svg instead of a .jpg")
    enc.add_argument("--seed", type=int, help="same seed + same text = same picture")
    enc.add_argument("--quiet", action="store_true", help="no progress bar")

    dec = sub.add_parser("decode", help="read the text back from a constellation SVG / JPG / PNG")
    dec.add_argument("image")
    dec.add_argument("-v", "--verbose", action="store_true", help="show what was read for every letter")

    sub.add_parser("alphabet", help="re-render alphabet/ pictures and RULES.md")

    args = ap.parse_args()
    if args.cmd == "encode":
        # the bar goes to stderr and only in a real terminal, so piping the file name stays clean
        print(encode_to(args.text, args.out, args.svg, args.seed, progress=sys.stderr.isatty() and not args.quiet))
    elif args.cmd == "decode":
        print(decode.decode(args.image, args.verbose))
    else:
        import make_alphabet
        make_alphabet.main()


if __name__ == "__main__":
    main()
