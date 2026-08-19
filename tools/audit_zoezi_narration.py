"""Audit book-wide Zoezi narration mappings for online and offline playback."""

import json
import re
from pathlib import Path

from rehema_speech import ZOEZI_PATTERN, normalize_global_narration


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    language = root / "content" / "i18n" / "sw-TZ"
    texts = json.loads((language / "texts.json").read_text())
    audios = json.loads((language / "audios.json").read_text())
    preloader = (root / "assets" / "offline-preloader.js").read_text()
    audio_dir = language / "audio"
    affected = sorted(
        text_id for text_id, text in texts.items() if ZOEZI_PATTERN.fullmatch(text)
    )

    if not affected:
        raise SystemExit("No numbered Zoezi labels found")

    failures: list[str] = []
    for text_id in affected:
        visible = texts[text_id]
        speech = normalize_global_narration(visible, text_id)
        filename = audios.get(text_id, "")
        path = audio_dir / filename
        mapping = f'"{text_id}":"{filename}"'

        if not re.fullmatch(rf"{re.escape(text_id)}_rehema_zoezi_v1\.mp3", filename):
            failures.append(f"{text_id}: unversioned mapping {filename!r}")
        if not path.is_file() or path.stat().st_size < 512:
            failures.append(f"{text_id}: missing or empty audio {filename!r}")
        if mapping not in preloader:
            failures.append(f"{text_id}: missing offline-preloader mapping")

        if not text_id.endswith("_easy_read"):
            page = root / f"{text_id[:5]}_sec001.html"
            if not page.is_file() or page.read_text().count(f'data-id="{text_id}"') != 1:
                failures.append(f"{text_id}: HTML must contain exactly one matching data-id")

        print(f"{text_id}: {visible!r} -> {speech!r} -> {filename}")

    stale_mappings = [
        text_id
        for text_id in affected
        if "_rehema_zoezi_v1.mp3" not in audios.get(text_id, "")
    ]
    if stale_mappings:
        failures.append(f"stale mapped IDs: {', '.join(stale_mappings)}")

    if failures:
        raise SystemExit("AUDIT FAILED\n" + "\n".join(failures))
    print(
        f"AUDIT PASS: {len(affected)} normal/Easy Read Zoezi clips; "
        "unique HTML IDs; synchronized online/offline mappings"
    )


if __name__ == "__main__":
    main()
