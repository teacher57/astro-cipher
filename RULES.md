# Astro cipher rules

- Every **letter or digit is one line between two big stars**. Words are chains of lines;
  the end star of one letter is the start star of the next.
- The **first star of every word has a Roman numeral next to it**: the word's position in the
  sentence: `I` for the first word, then `II`, `III`, ... Read a word by starting at its
  numbered star and walking the chain.
- Only two star sizes exist: **big** (letter boundaries) and **small** (what makes a letter unique).
- Small stars sit in six **slots** around each line:
  - `S` / `M` / `E`: near the **S**tart, the **M**iddle, or near the **E**nd of the line
  - `a` / `b`: **a**bove or **b**elow the line, where *above* = on your left while walking from
    the start star to the end star (on the key sheet every line runs left to right)
  - a number = how many small stars sit in that slot (1–3, side by side)
- Some letters also have a **form**:
  - `roofN`: a roof over the line with N small stars on top, joined to the big stars by strokes
    that point straight at them: 1 = one star, 2 = two stars joined by a dash, 3 = a zigzag of
    three (the middle one a bit lower). In messages the top stars sit at random distances and
    heights; every line keeps the same gap to the stars it points at.
  - `veeN`: the same shape hanging below the line
  - `double`: the line is drawn twice, side by side
  - `cross`: the line is crossed by a `//` mark in the middle
  - `solid`: the line's second star is filled in (only digits use it)
- A plain line with no small stars is **О / O**.
- Russian and English **look-alikes share one picture**: А=A, В=B, С=C, Е=E, Н=H, К=K, М=M, О=O, Р=P, Т=T, Х=X, У=Y.
  The decoder picks the alphabet from the other letters in the word (or else from the whole sentence).
- **Digits** end in a **solid** (filled-in) star, so they can never be mistaken for letters even when
  the shape matches one. `0` = bare line, `1`-`3` = roof of 1-3 stars above, `4`-`6` = vee of 1-3
  stars below, `7`-`9` = roof of 1-3 stars above on a double line.
- `Ё` is written as `Е`. Every other character (punctuation, dashes, emoji, ...) counts as a space between words.

See `alphabet/key_sheet.jpg` for all symbols, and `alphabet/{ru,en,digits}/` for one picture per symbol.

## Русский

| Symbol | Small stars | Same picture as |
|---|---|---|
| А | Sb1 | A |
| Б | roof1 Ma1 |  |
| В | Sa1 Sb1 | B |
| Г | vee1 Mb1 |  |
| Д | Ma3 Mb1 |  |
| Е | Ma1 | E |
| Ж | double |  |
| З | Ma3 |  |
| И | Sa1 Mb1 |  |
| Й | cross |  |
| К | vee1 | K |
| Л | Sb1 Mb1 |  |
| М | Ma2 Mb1 | M |
| Н | Ma1 Mb1 | H |
| О | plain line | O |
| П | roof1 |  |
| Р | Sa1 Ma1 | P |
| С | Mb3 | C |
| Т | Ea1 Eb1 | T |
| У | Ma2 | Y |
| Ф | roof1 vee1 |  |
| Х | Ma2 Mb2 | X |
| Ц | roof1 Eb1 |  |
| Ч | Ma2 Eb1 |  |
| Ш | roof2 |  |
| Щ | roof2 Eb1 |  |
| Ъ | roof2 Ma1 |  |
| Ы | Ea1 Sb1 |  |
| Ь | roof3 |  |
| Э | Mb1 |  |
| Ю | Mb2 |  |
| Я | Sa1 |  |

## English

| Symbol | Small stars | Same picture as |
|---|---|---|
| A | Sb1 | А |
| B | Sa1 Sb1 | В |
| C | Mb3 | С |
| D | roof1 Mb1 |  |
| E | Ma1 | Е |
| F | Eb1 |  |
| G | vee1 Ea1 |  |
| H | Ma1 Mb1 | Н |
| I | Eb2 |  |
| J | Sa1 Eb1 |  |
| K | vee1 | К |
| L | Ma1 Ea1 |  |
| M | Ma2 Mb1 | М |
| N | Ma1 Sb1 |  |
| O | plain line | О |
| P | Sa1 Ma1 | Р |
| Q | double Eb1 |  |
| R | Mb1 Eb1 |  |
| S | vee3 |  |
| T | Ea1 Eb1 | Т |
| U | vee2 |  |
| V | vee1 Sa1 |  |
| W | vee2 Ma1 |  |
| X | Ma2 Mb2 | Х |
| Y | Ma2 | У |
| Z | cross Sa1 Eb1 |  |

## Digits

| Symbol | Small stars | Same picture as |
|---|---|---|
| 0 | solid |  |
| 1 | roof1 solid |  |
| 2 | roof2 solid |  |
| 3 | roof3 solid |  |
| 4 | vee1 solid |  |
| 5 | vee2 solid |  |
| 6 | vee3 solid |  |
| 7 | roof1 double solid |  |
| 8 | roof2 double solid |  |
| 9 | roof3 double solid |  |

## Usage

```bash
astrocipher encode "i invented a cipher"             # -> <sha256 of the picture>.jpg here
astrocipher encode "look up tonight" --svg           # -> <sha256>.svg (vector image)
astrocipher encode "look up tonight" -o pics/        # -> pics/<sha256>.jpg
astrocipher encode "look up tonight" -o tonight.jpg  # -> exactly tonight.jpg (or .svg)
astrocipher decode <sha256>.jpg -v                   # reads .jpg, .svg or .png
astrocipher alphabet                                 # re-render alphabet/ and this file after editing alphabet.py
```

Pictures are named by the SHA-256 of their own bytes, so a file name never gives the message away.

Tests (pictures go to a temp folder, nothing is written to `out/`):

```bash
../.venv/bin/python test_roundtrip.py   # sample sentences, SVG + JPG
../.venv/bin/python test_angles.py      # every symbol alone at 24 angles
../.venv/bin/python test_stress.py      # many random layouts, with timing
```

`astrocipher` lives in `claude_trusted/.venv/bin/`, so it works whenever that venv is active.
