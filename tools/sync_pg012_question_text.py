"""Synchronize pg012's revised question with the offline reader cache."""

import json
from pathlib import Path


QUESTION = "1. Ni vitu gani unaviona/ unavyochunguza katika Kielelezo namba 5?"


def main():
    root = Path(__file__).resolve().parents[1]
    texts_path = root / "content" / "i18n" / "sw-TZ" / "texts.json"
    texts = json.loads(texts_path.read_text())
    texts["pg012_n0014"] = QUESTION
    texts["pg012_n0014_easy_read"] = QUESTION
    texts_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n")

    preloader_path = root / "assets" / "offline-preloader.js"
    preloader = preloader_path.read_text()
    replacements = {
        "1. Ni vitu gani unaviona katika Kielelezo namba 5?": QUESTION,
        "1. Unaona vitu gani katika Kielelezo namba 5?": QUESTION,
    }
    for old, new in replacements.items():
        if old not in preloader:
            raise SystemExit(f"Missing offline text: {old}")
        preloader = preloader.replace(old, new)
    preloader_path.write_text(preloader)


if __name__ == "__main__":
    main()
