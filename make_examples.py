"""Render the example pictures in examples/ and their index (examples/README.md), then check each one
decodes back to its text.

    python make_examples.py
"""
from pathlib import Path

import decode
import encode
from test_roundtrip import expected

HERE = Path(__file__).parent
OUT = HERE / "examples"

# (file name, text, seed): fixed seeds so the pictures can be rebuilt exactly
EXAMPLES = [
    ("hello_world", "hello world", 1),
    ("look_up_tonight", "look up tonight", 2),
    ("the_stars_keep_our_secrets", "the stars keep our secrets", 3),
    ("meet_me_at_the_old_oak_at_9", "meet me at the old oak at 9", 4),
    ("i_invented_a_cipher_in_2026", "i invented a cipher in 2026", 5),
    ("orion_rises_at_10_pm", "Orion rises at 10 PM, bring a blanket!", 6),
]


def main():
    OUT.mkdir(exist_ok=True)
    rows = []
    for name, text, seed in EXAMPLES:
        path = OUT / f"{name}.jpg"
        encode.encode(text, path, seed=seed)
        got = decode.decode(path)
        assert got == expected(text), f"{name}: decoded {got!r}"
        rows.append(f"| [{name}.jpg]({name}.jpg) | {text} | `{got}` | {seed} |")
        print(f"ok  {path.name}: {got}")
    (OUT / "README.md").write_text("\n".join([
        "# Examples",
        "",
        "Each picture below was made with `astrocipher encode` and decodes back to the text next to it.",
        "Try reading one with the [key sheet](../alphabet/key_sheet.jpg) before you look!",
        "",
        "| Picture | Text | What the decoder reads | Seed |",
        "|---|---|---|---|",
        *rows,
        "",
        "Punctuation counts as a space, so it disappears from the decoded text, and letters come back",
        "in capitals. Rebuild them all with `python make_examples.py`; the seed makes each picture exactly",
        "the same every time.",
        "",
    ]))


if __name__ == "__main__":
    main()
