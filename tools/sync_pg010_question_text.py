"""Synchronize pg010's revised question with the offline reader cache."""

import json
from pathlib import Path


QUESTION = "1. Bainisha vitu vya asili na visivyo vya asili ulivyoviona/ ulivyochunguza"


def main():
    root = Path(__file__).resolve().parents[1]
    texts_path = root / "content" / "i18n" / "sw-TZ" / "texts.json"
    texts = json.loads(texts_path.read_text())
    texts["pg010_n0008"] = QUESTION
    texts["pg010_n0008_easy_read"] = QUESTION
    texts_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n")

    preloader_path = root / "assets" / "offline-preloader.js"
    preloader = preloader_path.read_text()
    old = "1. Bainisha vitu vya asili na visivyo vya asili ulivyoviona/ ulivyochunguza; na"
    if old not in preloader:
        raise SystemExit(f"Missing offline text: {old}")
    preloader = preloader.replace(old, QUESTION)
    preloader_path.write_text(preloader)


if __name__ == "__main__":
    main()
