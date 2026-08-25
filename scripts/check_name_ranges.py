#!/usr/bin/env python3
"""Verify that every śloka carries exactly its own names.

The 1000 names in scripts/source/names_1000.json run in the same order as the
ślokas they are drawn from, so the grouping in build_data.NAME_RANGES can be
checked mechanically: strip both the śloka and its names down to a consonant
skeleton (transliterations differ — "Bhootha" / "bhūta", "Dur Jaya" / "durjayo")
and the names of a śloka, joined end to end, should read back as the śloka
itself. A drift of one name shows up as a large edit distance.

Run: python3 scripts/check_name_ranges.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_data import NAME_RANGES, NAMES_JSON, OUT  # noqa: E402

VOWELS = set("aeiou")
VOICING = str.maketrans({"g": "k", "j": "c", "d": "t", "b": "p", "m": "n", "l": "r"})
# Tolerance per śloka: transliteration noise, not a misplaced name.
MAX_DISTANCE = 8


def skeleton(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"[^a-z]+", "", text)
    text = text.replace("ksh", "ks").replace("chh", "c").replace("ch", "c")
    text = text.replace("sh", "s").replace("jn", "gn")
    for letter in "kgcjtdpbrnm":
        text = text.replace(letter + "h", letter)
    text = text.replace("w", "v").replace("y", "").replace("h", "")
    text = "".join(c for c in text if c not in VOWELS)
    return text.translate(VOICING)


def collapse(text: str) -> str:
    return re.sub(r"(.)\1+", r"\1", text)


def distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return prev[len(b)]


def main() -> int:
    names = json.loads(NAMES_JSON.read_text(encoding="utf-8"))
    payload = json.loads(OUT.read_text(encoding="utf-8").split("=", 1)[1].strip().rstrip(";"))
    verses = [v for v in payload["learn"] if v["section"] == "stotram"]

    problems: list[str] = []

    expected = 1
    for i, (start, end) in enumerate(NAME_RANGES, 1):
        if start != expected:
            problems.append(f"śloka {i}: starts at {start}, expected {expected}")
        expected = end + 1
    if expected != 1001:
        problems.append(f"the ranges cover {expected - 1} names, expected 1000")

    for i, (start, end) in enumerate(NAME_RANGES):
        verse = verses[i]
        joined = collapse("".join(skeleton(names[n - 1]["name"]) for n in range(start, end + 1)))
        # Śloka 107 repeats its last name in the "oṃ nama iti" tail she sings
        # before the pause; that repetition is not a 1001st name.
        iast = re.sub(r"\|\|\s*107\s*\|\|.*", "", verse["iast"])
        spoken = collapse(skeleton(iast))
        d = distance(joined, spoken)
        if d > MAX_DISTANCE:
            problems.append(
                f"śloka {i + 1}: names {start}–{end} do not read back as the verse "
                f"(edit distance {d} over {len(spoken)} letters)"
            )

    for verse in verses:
        got = [n["n"] for n in verse["names"]]
        if got and got != list(range(got[0], got[0] + len(got))):
            problems.append(f"śloka {verse.get('shloka')}: name numbers are not consecutive")

    if problems:
        print("\n".join(problems))
        print(f"\n{len(problems)} problem(s).")
        return 1
    print(f"All {len(NAME_RANGES)} ślokas carry their own names; 1000 names accounted for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
