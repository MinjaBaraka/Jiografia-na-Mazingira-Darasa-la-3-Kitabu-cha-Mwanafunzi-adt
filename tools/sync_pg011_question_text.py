"""Synchronize pg011's revised question with the offline reader cache."""

import json
from pathlib import Path


QUESTION = "1. Ni vitu gani unaviona/ unavyochunguza katika Kielelezo namba 4?"


def main():
    root = Path(__file__).resolve().parents[1]
    texts_path = root / "content" / "i18n" / "sw-TZ" / "texts.json"
    texts = json.loads(texts_path.read_text())
    texts["pg011_n0010"] = QUESTION
    texts["pg011_n0010_easy_read"] = QUESTION
    texts_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n")

    preloader_path = root / "assets" / "offline-preloader.js"
    preloader = preloader_path.read_text()
    for old in (
        "1. Ni vitu gani unaviona katika Kielelezo namba 4?",
        "1. Unaona vitu gani katika Kielelezo namba 4?",
    ):
        if old not in preloader:
            raise SystemExit(f"Missing offline text: {old}")
        preloader = preloader.replace(old, QUESTION)
    preloader_path.write_text(preloader)


if __name__ == "__main__":
    main()
