# Astro Cipher

Hide text in a picture of the night sky. Every letter is a line between two big stars; small stars,
roofs and other little marks around the line tell the letters apart. Words are chains of stars, numbered
with Roman numerals. To anyone without the key, it's just a constellation.

![English key sheet](alphabet/key_sheet_en.jpg)

- **Every picture is different:** line lengths, turns, roof heights and spacing are random; `--seed` repeats one.
- **Decoder reads the pixels** of a JPG, PNG or SVG made by the encoder: it finds the stars, lines and
  numerals and walks each word from its numbered star.
- Punctuation counts as a space.

The full rules, with a table for every symbol, are in [RULES.md](RULES.md).

## Examples

![hello world](examples/hello_world.jpg)

Six English messages with their text, from "hello world" to one with punctuation, are in
[examples/](examples/README.md). Try reading one with the key sheet before you look at the answer.

## Usage

```bash
pip install -r requirements.txt

./astrocipher encode "i invented a cipher"             # -> <sha256 of the picture>.jpg, with a progress bar
./astrocipher encode "look up tonight" --svg           # -> <sha256>.svg (vector image)
./astrocipher encode "look up tonight" -o tonight.jpg  # -> exactly that file name
./astrocipher decode tonight.jpg -v                    # prints the text; -v shows what was read per letter
./astrocipher alphabet                                 # re-renders alphabet/ and RULES.md after editing alphabet.py
```

Files are named by the SHA-256 of their own bytes, so a file name never gives the message away.
The fonts used for numerals and the key sheet are macOS system fonts (Times New Roman, Arial Unicode).

## Files

| File | What it does |
|---|---|
| `alphabet.py` | the cipher's rules: which marks make up every symbol |
| `encode.py` | random constellation layout and drawing (JPG or SVG) |
| `decode.py` | reads a picture back into text |
| `cli.py`, `astrocipher` | the `astrocipher` command |
| `make_alphabet.py` | renders `alphabet/` (one picture per symbol, key sheet) and `RULES.md` |
| `make_examples.py`, `examples/` | example pictures with their text, rebuilt and checked by the script |
| `ideas/` | design mock-ups explored for the cipher's symbols |

## Tests

```bash
python test_roundtrip.py   # sample sentences, SVG + JPG
python test_angles.py      # every symbol alone at 24 angles with random shapes
python test_stress.py      # many random layouts, with timing
```

## License

MIT, see [LICENSE](LICENSE).

AI friendly: built together with Claude.
