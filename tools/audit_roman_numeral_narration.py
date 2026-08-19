"""Audit Roman-numeral narration coverage across the exported ADT book."""

import json
import re
from pathlib import Path

from rehema_speech import PG013_FIRST_EXERCISE_IDS, ROMAN_PATTERN, normalize_global_narration


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    language = root / "content" / "i18n" / "sw-TZ"
    texts = json.loads((language / "texts.json").read_text())
    audios = json.loads((language / "audios.json").read_text())
    html = "\n".join(path.read_text() for path in sorted(root.glob("*.html")))
    preloader = (root / "assets" / "offline-preloader.js").read_text()

    affected = sorted(text_id for text_id, text in texts.items() if ROMAN_PATTERN.search(text))
    expected_ids = affected + sorted(PG013_FIRST_EXERCISE_IDS)
    failures: list[str] = []

    for text_id in expected_ids:
        text = texts.get(text_id)
        filename = audios.get(text_id)
        if text is None:
            failures.append(f"missing text: {text_id}")
            continue
        if not filename:
            failures.append(f"missing audio mapping: {text_id}")
            continue
        audio_path = language / "audio" / filename
        if not audio_path.exists() or audio_path.stat().st_size < 512:
            failures.append(f"missing/empty audio file: {text_id} -> {filename}")
        offline_mapping = f'"{text_id}":"{filename}"'
        offline_occurrences = preloader.count(offline_mapping)
        if offline_occurrences != 1:
            failures.append(
                f"offline mapping occurs {offline_occurrences} times: {text_id} -> {filename}"
            )
        print(f"{text_id}\t{filename}\t{normalize_global_narration(text, text_id)}")

    base_ids = [text_id for text_id in affected if not text_id.endswith("_easy_read")]
    for text_id in base_ids:
        occurrences = len(re.findall(rf'data-id=["\']{re.escape(text_id)}["\']', html))
        if occurrences != 1:
            failures.append(f"HTML data-id occurs {occurrences} times: {text_id}")

    print(
        f"AUDIT: {len(base_ids)} visible Roman numerals; "
        f"{len(affected)} normal/Easy Read Roman clips; "
        f"{len(PG013_FIRST_EXERCISE_IDS)} pg013 exercise clips"
    )
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
