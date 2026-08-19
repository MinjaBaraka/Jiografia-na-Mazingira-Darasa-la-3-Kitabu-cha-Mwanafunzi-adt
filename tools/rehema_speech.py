"""Book-wide speech normalization for Rehema Natural sw-TZ narration."""

import re


ROMAN_NUMBERS = {
    "i": "moja",
    "ii": "mbili",
    "iii": "tatu",
    "iv": "nne",
    "v": "tano",
    "vi": "sita",
    "vii": "saba",
    "viii": "nane",
    "ix": "tisa",
    "x": "kumi",
    "xi": "kumi na moja",
    "xii": "kumi na mbili",
    "xiii": "kumi na tatu",
    "xiv": "kumi na nne",
    "xv": "kumi na tano",
    "xvi": "kumi na sita",
    "xvii": "kumi na saba",
    "xviii": "kumi na nane",
    "xix": "kumi na tisa",
    "xx": "ishirini",
}

ROMAN_PATTERN = re.compile(
    r"\((?P<roman>xx|xix|xviii|xvii|xvi|xv|xiv|xiii|xii|xi|x|ix|viii|vii|vi|v|iv|iii|ii|i)\)(?:\s*\.)?",
    flags=re.IGNORECASE,
)

ZOEZI_ORDINALS = {
    1: "kwanza",
    2: "pili",
    3: "tatu",
    4: "nne",
    5: "tano",
    6: "sita",
    7: "saba",
    8: "nane",
    9: "tisa",
    10: "kumi",
}

ZOEZI_PATTERN = re.compile(r"^\s*Zoezi la\s+(?P<number>\d+)\s*\.?\s*$", re.IGNORECASE)

# Kept for compatibility with the earlier Roman-numeral versioning utility.
PG013_FIRST_EXERCISE_IDS = {"pg013_n0008", "pg013_n0008_easy_read"}


def normalize_global_narration(text: str, text_id: str) -> str:
    """Return speech-only wording without changing the visible textbook text."""
    exercise = ZOEZI_PATTERN.fullmatch(text)
    if exercise:
        number = int(exercise.group("number"))
        if ordinal := ZOEZI_ORDINALS.get(number):
            return f"Zoezi la {ordinal}."

    return ROMAN_PATTERN.sub(
        lambda match: f"Namba za kirumi {ROMAN_NUMBERS[match.group('roman').lower()]}.",
        text,
    )
