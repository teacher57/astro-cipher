"""Astro cipher alphabet.

Every symbol is one line between two big stars, read from the start star to the end star.
Small stars in six slots around the line tell symbols apart:

    S / M / E  = near the Start, the Middle, or near the End of the line
    a / b      = above / below the line (above = on your left when walking start -> end)

A code like "Sa1 Mb2" means 1 small star above-start and 2 small stars below-middle.
An empty code is a plain line. Russian and English look-alikes (А/A, В/B, ...) share one code.

Complex forms on top of the slots:

    roofN   a roof over the line (two slanted strokes) with N small stars at its top
            (1 = single apex, 2 = two stars joined by a dash, 3 = zigzag)
    veeN    the same shape hanging below the line
    double  the line is drawn twice, side by side
    cross   the line is crossed by a "//" mark in the middle
    hollow  the line's second (end) star is left empty (every other star is filled): this marks a digit
"""

SLOTS = ("Sa", "Ma", "Ea", "Sb", "Mb", "Eb")
FORMS = ("roof", "vee", "double", "cross", "hollow")
FEATURES = SLOTS + FORMS

# slots a form would collide with when drawn
BLOCKS = {"roof": {"Sa", "Ea"}, "vee": {"Sb", "Eb"}, "cross": {"Ma", "Mb"}}

RU = {
    "А": "Sb1",
    "Б": "roof1 Ma1",
    "В": "Sa1 Sb1",
    "Г": "vee1 Mb1",
    "Д": "Ma3 Mb1",
    "Е": "Ma1",
    "Ж": "double",
    "З": "Ma3",
    "И": "Sa1 Mb1",
    "Й": "cross",
    "К": "vee1",
    "Л": "Sb1 Mb1",
    "М": "Ma2 Mb1",
    "Н": "Ma1 Mb1",
    "О": "",
    "П": "roof1",
    "Р": "Sa1 Ma1",
    "С": "Mb3",
    "Т": "Ea1 Eb1",
    "У": "Ma2",
    "Ф": "roof1 vee1",
    "Х": "Ma2 Mb2",
    "Ц": "roof1 Eb1",
    "Ч": "Ma2 Eb1",
    "Ш": "roof2",
    "Щ": "roof2 Eb1",
    "Ъ": "roof2 Ma1",
    "Ы": "Sb1 Ea1",
    "Ь": "roof3",
    "Э": "Mb1",
    "Ю": "Mb2",
    "Я": "Sa1",
}

# English letters that look like a Russian one reuse its code.
EN_SHARED = {
    "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "K": "К",
    "M": "М", "O": "О", "P": "Р", "T": "Т", "X": "Х", "Y": "У",
}

EN_OWN = {
    "D": "roof1 Mb1",
    "F": "Eb1",
    "G": "vee1 Ea1",
    "I": "Eb2",
    "J": "Sa1 Eb1",
    "L": "Ma1 Ea1",
    "N": "Ma1 Sb1",
    "Q": "double Eb1",
    "R": "Mb1 Eb1",
    "S": "vee3",
    "U": "vee2",
    "V": "vee1 Sa1",
    "W": "vee2 Ma1",
    "Z": "cross Sa1 Eb1",
}

# Digits: the line ends in a hollow star. 0 = bare line, 1-3 = roof of 1-3 stars above,
# 4-6 = vee of 1-3 stars below, 7-9 = roof of 1-3 stars above on a double line.
DIGITS = {
    "0": "hollow", "1": "hollow roof1", "2": "hollow roof2", "3": "hollow roof3",
    "4": "hollow vee1", "5": "hollow vee2", "6": "hollow vee3",
    "7": "hollow double roof1", "8": "hollow double roof2", "9": "hollow double roof3",
}

NORMALIZE = {"Ё": "Е"}


def parse(code):
    """'roof1 Mb2' -> {'roof': 1, 'Mb': 2}"""
    out = {}
    for tok in code.split():
        name = tok.rstrip("0123456789")
        n = int(tok[len(name):] or 1)
        assert name in FEATURES and 1 <= n <= 3, tok
        out[name] = out.get(name, 0) + n
    for form, slots in BLOCKS.items():
        assert not (out.get(form) and slots & out.keys()), f"{code}: {form} collides with {slots & out.keys()}"
    assert not (out.get("roof") == 3 and out.get("Ma")), f"{code}: zigzag roof collides with Ma"
    assert not (out.get("vee") == 3 and out.get("Mb")), f"{code}: zigzag vee collides with Mb"
    return out


def key(counts):
    """Hashable form of a feature->count dict."""
    return tuple(counts.get(f, 0) for f in FEATURES)


def fmt(counts):
    return " ".join(f if f in ("double", "cross", "hollow") else f"{f}{counts[f]}" for f in FORMS + SLOTS if counts.get(f))


def _build():
    codes, script = {}, {}
    for ch, c in RU.items():
        codes[ch], script[ch] = parse(c), "ru"
    for ch, ru in EN_SHARED.items():
        codes[ch], script[ch] = codes[ru], "en"
    for ch, c in EN_OWN.items():
        codes[ch], script[ch] = parse(c), "en"
    for ch, code in DIGITS.items():
        codes[ch], script[ch] = parse(code), "digit"

    decode = {}
    for ch, c in codes.items():
        decode.setdefault(key(c), []).append(ch)
    for k, chars in decode.items():
        shared = len(chars) == 2 and EN_SHARED.get(chars[1]) == chars[0]
        assert len(chars) == 1 or shared, f"code clash: {chars}"
    return codes, script, decode


CODES, SCRIPT, DECODE = _build()


def normalize(ch):
    ch = ch.upper()
    return NORMALIZE.get(ch, ch)


def tokenize(text):
    """Split text into words of encodable symbols; every character without a symbol
    (punctuation, dashes, emoji, ...) counts as a space. Returns (words, replaced_chars)."""
    clean, replaced = [], set()
    for ch in text:
        ch = normalize(ch)
        if ch in CODES:
            clean.append(ch)
        else:
            clean.append(" ")
            if not ch.isspace():
                replaced.add(ch)
    return [list(w) for w in "".join(clean).split()], replaced
