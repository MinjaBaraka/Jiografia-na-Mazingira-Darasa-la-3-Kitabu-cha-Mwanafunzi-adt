"""Version audited Roman-numeral audio so online caches cannot reuse old clips."""

import json
from pathlib import Path

from rehema_speech import PG013_FIRST_EXERCISE_IDS, ROMAN_PATTERN


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    language = root / "content" / "i18n" / "sw-TZ"
    texts = json.loads((language / "texts.json").read_text())
    audio_map_path = language / "audios.json"
    audios = json.loads(audio_map_path.read_text())
    audio_dir = language / "audio"
    preloader_path = root / "assets" / "offline-preloader.js"
    preloader = preloader_path.read_text()

    roman_ids = {text_id for text_id, text in texts.items() if ROMAN_PATTERN.search(text)}
    affected = sorted(roman_ids | PG013_FIRST_EXERCISE_IDS)
    for text_id in affected:
        old_name = audios[text_id]
        suffix = "roman_v1" if text_id in roman_ids else "ordinal_v1"
        new_name = f"{text_id}_rehema_{suffix}.mp3"
        old_path = audio_dir / old_name
        new_path = audio_dir / new_name

        if old_name != new_name:
            if not old_path.exists():
                raise SystemExit(f"Missing source audio: {old_path}")
            if new_path.exists():
                raise SystemExit(f"Versioned audio already exists: {new_path}")
            old_path.replace(new_path)
            audios[text_id] = new_name

            old_mapping = f'"{text_id}":"{old_name}"'
            new_mapping = f'"{text_id}":"{new_name}"'
            if old_mapping not in preloader:
                raise SystemExit(f"Missing offline mapping: {text_id}")
            preloader = preloader.replace(old_mapping, new_mapping, 1)

    audio_map_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n")
    preloader_path.write_text(preloader)
    print(f"Versioned {len(affected)} Rehema narration clips")


if __name__ == "__main__":
    main()
