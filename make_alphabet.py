"""Render one JPG per symbol (alphabet/ru, alphabet/en, alphabet/digits), a combined
key sheet (alphabet/key_sheet.jpg) and the rules table (RULES.md).

    python make_alphabet.py
"""
from pathlib import Path

import alphabet as ab
import encode as en

HERE = Path(__file__).parent
CELL_H = 210

# folder, title, symbols, columns on the key sheet
SECTIONS = [
    ("ru", "Русский", list(ab.RU), 3),
    ("en", "English", [chr(c) for c in range(ord("A"), ord("Z") + 1)], 3),
    ("digits", "Digits", list(ab.DIGITS), 3),
]


def cell_h(chars):
    return CELL_H


def cell_w(chars):
    """Cell width that fits the longest line among these symbols."""
    return 170 + max(en.key_edge(ch) for ch in chars) + 70


def caption(ch, twins=True):
    """'А = A' for look-alikes (unless `twins` is off), else just the symbol."""
    if not twins:
        return ch
    if ch in ab.EN_SHARED:
        return f"{ch} = {ab.EN_SHARED[ch]}"
    twin = next((e for e, r in ab.EN_SHARED.items() if r == ch), None)
    return f"{ch} = {twin}" if twin else ch


def draw_cell(sheet, x, y, ch, twins=True):
    mid = y + cell_h([ch]) / 2
    text = caption(ch, twins)
    sheet.text((x + 75, mid), text, 34 if len(text) > 1 else 54)
    a = (x + 170, mid)
    b = (a[0] + en.key_edge(ch), a[1])
    en.draw_letter(sheet, a, b, ch)
    sheet.star(a, big=True)
    sheet.star(b, big=True, hollow=bool(ab.CODES[ch].get("hollow")))


def key_sheet(sections, path, twins=True):
    """All symbols of `sections` on one picture, a titled block per section."""
    head = 80
    width = max(cell_w(chars) * cols for _, _, chars, cols in sections)
    height = sum(-(-len(chars) // cols) * cell_h(chars) for _, _, chars, cols in sections)
    sheet = en.Sheet(width, height + head * len(sections) + 40)
    y = 20
    for _, title, chars, cols in sections:
        sheet.text((width / 2, y + head / 2), title, 44)
        y += head
        cw, ch_ = cell_w(chars), cell_h(chars)
        for i, ch in enumerate(chars):
            draw_cell(sheet, (i % cols) * cw, y + (i // cols) * ch_, ch, twins)
        y += -(-len(chars) // cols) * ch_
    sheet.save(path)


def main():
    for folder, _, chars, _ in SECTIONS:
        for i, ch in enumerate(chars, 1):
            sheet = en.Sheet(cell_w([ch]), cell_h([ch]))
            draw_cell(sheet, 0, 0, ch)
            name = f"{ch}.jpg" if folder == "digits" else f"{i:02d}_{ch}.jpg"
            sheet.save(HERE / "alphabet" / folder / name)

    key_sheet(SECTIONS, HERE / "alphabet" / "key_sheet.jpg")
    # English letters only, plain captions (no Cyrillic twins): the one shown in the README
    key_sheet([sec for sec in SECTIONS if sec[0] == "en"], HERE / "alphabet" / "key_sheet_en.jpg", twins=False)

    lines = [
        "# Astro cipher rules",
        "",
        "- Every **letter or digit is one line between two big stars**. Words are chains of lines;",
        "  the end star of one letter is the start star of the next.",
        "- The **first star of every word has a Roman numeral next to it**: the word's position in the",
        "  sentence: `I` for the first word, then `II`, `III`, ... Read a word by starting at its",
        "  numbered star and walking the chain.",
        "- Only two star sizes exist: **big** (letter boundaries) and **small** (what makes a letter unique).",
        "- Small stars sit in six **slots** around each line:",
        "  - `S` / `M` / `E`: near the **S**tart, the **M**iddle, or near the **E**nd of the line",
        "  - `a` / `b`: **a**bove or **b**elow the line, where *above* = on your left while walking from",
        "    the start star to the end star (on the key sheet every line runs left to right)",
        "  - a number = how many small stars sit in that slot (1–3, side by side)",
        "- Some letters also have a **form**:",
        "  - `roofN`: a roof over the line with N small stars on top, joined to the big stars by strokes",
        "    that point straight at them: 1 = one star, 2 = two stars joined by a dash, 3 = a zigzag of",
        "    three (the middle one a bit lower). In messages the top stars sit at random distances and",
        "    heights; every line keeps the same gap to the stars it points at.",
        "  - `veeN`: the same shape hanging below the line",
        "  - `double`: the line is drawn twice, side by side",
        "  - `cross`: the line is crossed by a `//` mark in the middle",
        "  - `hollow`: the line's second star is left empty inside (only digits use it)",
        "- A plain line with no small stars is **О / O**.",
        "- Russian and English **look-alikes share one picture**: " +
        ", ".join(f"{r}={e}" for e, r in ab.EN_SHARED.items()) + ".",
        "  The decoder picks the alphabet from the other letters in the word (or else from the whole sentence).",
        "- Every star is **filled white**, except a digit's second star, which is **hollow** (dark inside), so",
        "  digits can never be mistaken for letters even when",
        "  the shape matches one. `0` = bare line, `1`-`3` = roof of 1-3 stars above, `4`-`6` = vee of 1-3",
        "  stars below, `7`-`9` = roof of 1-3 stars above on a double line.",
        "- `Ё` is written as `Е`. Every other character (punctuation, dashes, emoji, ...) counts as a space between words.",
        "",
        "See `alphabet/key_sheet.jpg` for all symbols, and `alphabet/{ru,en,digits}/` for one picture per symbol.",
        "",
    ]
    for _, title, chars, _ in SECTIONS:
        lines += [f"## {title}", "", "| Symbol | Small stars | Same picture as |", "|---|---|---|"]
        for ch in chars:
            twin = ab.EN_SHARED.get(ch) or next((e for e, r in ab.EN_SHARED.items() if r == ch), "")
            lines.append(f"| {ch} | {ab.fmt(ab.CODES[ch]) or 'plain line'} | {twin} |")
        lines.append("")
    lines += [
        "## Usage",
        "",
        "```bash",
        "astrocipher encode \"i invented a cipher\"             # -> <sha256 of the picture>.jpg here",
        "astrocipher encode \"look up tonight\" --svg           # -> <sha256>.svg (vector image)",
        "astrocipher encode \"look up tonight\" -o pics/        # -> pics/<sha256>.jpg",
        "astrocipher encode \"look up tonight\" -o tonight.jpg  # -> exactly tonight.jpg (or .svg)",
        "astrocipher decode <sha256>.jpg -v                   # reads .jpg, .svg or .png",
        "astrocipher alphabet                                 # re-render alphabet/ and this file after editing alphabet.py",
        "```",
        "",
        "Pictures are named by the SHA-256 of their own bytes, so a file name never gives the message away.",
        "",
        "Tests (pictures go to a temp folder, nothing is written to `out/`):",
        "",
        "```bash",
        "../.venv/bin/python test_roundtrip.py   # sample sentences, SVG + JPG",
        "../.venv/bin/python test_angles.py      # every symbol alone at 24 angles",
        "../.venv/bin/python test_stress.py      # many random layouts, with timing",
        "```",
        "",
        "`astrocipher` lives in `claude_trusted/.venv/bin/`, so it works whenever that venv is active.",
        "",
    ]
    (HERE / "RULES.md").write_text("\n".join(lines))
    print("wrote alphabet/ and RULES.md")


if __name__ == "__main__":
    main()
