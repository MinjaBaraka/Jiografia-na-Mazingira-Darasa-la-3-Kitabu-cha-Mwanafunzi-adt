"""Audit pg009 Figure 3 descriptions and Rehema clips for online/offline use."""

from __future__ import annotations

import json
from pathlib import Path

from fix_pg009_figure3_rehema import LANGUAGE, ROOT, TARGET_IDS, VERSION


def main() -> None:
    texts = json.loads((LANGUAGE / "texts.json").read_text())
    audios = json.loads((LANGUAGE / "audios.json").read_text())
    audio_dir = LANGUAGE / "audio"
    problems: list[str] = []

    for text_id in TARGET_IDS:
        if not texts[text_id].lower().startswith(
            "picha katika kielelezo namba 3"
        ):
            problems.append(f"{text_id}: incorrect Figure 3 description")
        expected_name = f"{text_id}_{VERSION}.mp3"
        if audios.get(text_id) != expected_name:
            problems.append(f"{text_id}: stale audio mapping")
        path = audio_dir / expected_name
        if not path.is_file() or path.stat().st_size < 512:
            problems.append(f"{text_id}: missing or empty Rehema clip")
        stale = [
            item.name for item in audio_dir.glob(f"{text_id}*.mp3")
            if item.name != expected_name
        ]
        if stale:
            problems.append(f"{text_id}: stale clips remain: {stale}")

    preloader_path = ROOT / "assets" / "offline-preloader.js"
    source = preloader_path.read_text()
    marker = "  var INLINE = "
    end_marker = ";\n  var BASE_DIR"
    start = source.index(marker) + len(marker)
    end = source.index(end_marker, start)
    inline = json.loads(source[start:end])
    if inline.get("./content/i18n/sw-TZ/texts.json") != texts:
        problems.append("offline texts.json is stale")
    if inline.get("./content/i18n/sw-TZ/audios.json") != audios:
        problems.append("offline audios.json is stale")
    page = (ROOT / "pg009_sec001.html").read_text()
    if inline.get("./pg009_sec001.html") != page:
        problems.append("offline pg009 HTML is stale")
    if "offline-preloader.js?v=pg009-figure3-rehema-v2" not in page:
        problems.append("pg009 cache-buster is stale")

    if problems:
        raise SystemExit("\n".join(problems))
    print("AUDIT PASS: six pg009 Figure 3 descriptions use new Rehema v2 clips")


if __name__ == "__main__":
    main()
