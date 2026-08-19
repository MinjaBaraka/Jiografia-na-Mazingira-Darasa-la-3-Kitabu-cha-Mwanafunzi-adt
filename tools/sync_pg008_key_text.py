"""Synchronize the pg008 map-key colour labels with the offline reader."""

import json
from pathlib import Path


LABELS = {
    "pg008_n0007": "Mabara",
    "pg008_n0008": "Bahari",
    "pg008_n0007_easy_read": "Mabara",
    "pg008_n0008_easy_read": "Bahari",
}


def main():
    root = Path(__file__).resolve().parents[1]
    language = root / "content" / "i18n" / "sw-TZ"
    texts_path = language / "texts.json"
    texts = json.loads(texts_path.read_text())
    texts.update(LABELS)
    texts_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n")

    preloader_path = root / "assets" / "offline-preloader.js"
    preloader = preloader_path.read_text()
    for text_id, label in LABELS.items():
        old_label = "Mabara — rangi ya kijani" if "n0007" in text_id else "Bahari — rangi ya bluu"
        old = f'"{text_id}":"{old_label}"'
        if old not in preloader:
            raise SystemExit(f"Missing offline text: {text_id}")
        preloader = preloader.replace(old, f'"{text_id}":"{label}"', 1)
    preloader_path.write_text(preloader)


if __name__ == "__main__":
    main()
