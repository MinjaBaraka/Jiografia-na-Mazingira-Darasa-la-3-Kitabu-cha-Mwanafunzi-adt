"""Keep only the Rehema diagram description for Kielelezo namba 2."""

import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    language = root / "content" / "i18n" / "sw-TZ"
    audio_map_path = language / "audios.json"
    audios = json.loads(audio_map_path.read_text())
    removed = {}
    for text_id in (
        "pg009_n0004", "pg009_n0005", "pg009_n0006", "pg009_n0007", "pg009_n0008",
        "pg009_n0004_easy_read", "pg009_n0005_easy_read", "pg009_n0006_easy_read",
        "pg009_n0007_easy_read", "pg009_n0008_easy_read",
        "pg009_n0009", "pg009_n0009_easy_read",
    ):
        filename = audios.pop(text_id, None)
        if filename is not None:
            removed[text_id] = filename
    audio_map_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n")

    preloader_path = root / "assets" / "offline-preloader.js"
    preloader = preloader_path.read_text()
    for text_id, filename in removed.items():
        entry = f'"{text_id}":"{filename}",'
        if entry not in preloader:
            raise SystemExit(f"Missing offline audio mapping: {text_id}")
        preloader = preloader.replace(entry, "", 1)
        path = language / "audio" / filename
        if not path.is_file():
            raise SystemExit(f"Missing audio file: {path}")
        path.unlink()
    preloader_path.write_text(preloader)


if __name__ == "__main__":
    main()
