"""Verify every Yaliyomo number/link matches the ADT x/88 navigation index."""

from __future__ import annotations

import hashlib
import json
import re

from fix_yaliyomo_navigation import LANGUAGE, ROOT, TOC_ROWS, VERSION


def legacy_name(text_id: str) -> str:
    special = {
        "pg003_n0006": "pg003_n0006_rehema.mp3",
        "pg003_n0009": "pg003_n0009_rehema.mp3",
        "pg003_n0006_easy_read": "pg003_n0006_easy_read_rehema.mp3",
        "pg003_n0009_easy_read": "pg003_n0009_easy_read_rehema.mp3",
    }
    return special.get(text_id, f"{text_id}.mp3")


def main() -> None:
    pages = json.loads((ROOT / "content" / "pages.json").read_text())
    texts = json.loads((LANGUAGE / "texts.json").read_text())
    audios = json.loads((LANGUAGE / "audios.json").read_text())
    html = (ROOT / "pg003_sec001.html").read_text()
    audio_dir = LANGUAGE / "audio"
    problems: list[str] = []

    if len(pages) != 88:
        problems.append(f"pages.json has {len(pages)} entries, expected 88")
    page_index = {entry["href"]: number for number, entry in enumerate(pages, 1)}

    for title_id, number_id, title, number, target in TOC_ROWS:
        if page_index.get(target) != number:
            problems.append(f"{title}: {target} is {page_index.get(target)}/88, not {number}/88")
        target_html = (ROOT / target).read_text()
        meta = re.search(r'<meta name="page-section-id" content="(\d+)"', target_html)
        if not meta or int(meta.group(1)) != number:
            problems.append(f"{title}: target HTML navigation metadata is not {number}")

        row = re.search(
            rf'<a href="\./{re.escape(target)}" data-adt-page="{number}"[^>]*'
            rf'aria-label="{re.escape(title)} {number}">(?P<body>.*?)</a>',
            html,
            re.DOTALL,
        )
        if not row:
            problems.append(f"{title}: missing or incorrect Yaliyomo link")
        else:
            body = row.group("body")
            if not re.search(
                rf'data-id="{re.escape(number_id)}"[^>]*>\s*{number}\s*</span>',
                body,
            ):
                problems.append(f"{title}: displayed number does not equal {number}")

        for suffix in ("", "_easy_read"):
            current_number_id = f"{number_id}{suffix}"
            if texts.get(current_number_id) != str(number):
                problems.append(f"{current_number_id}: texts.json is not {number}")

    target_ids = [
        text_id for text_id in texts
        if text_id.startswith("pg003_") and text_id in audios
    ]
    for text_id in target_ids:
        expected_name = f"{text_id}_{VERSION}.mp3"
        if audios.get(text_id) != expected_name:
            problems.append(f"{text_id}: current Rehema mapping is stale")
            continue
        current = audio_dir / expected_name
        legacy = audio_dir / legacy_name(text_id)
        if not current.is_file() or current.stat().st_size < 512:
            problems.append(f"{text_id}: new Rehema audio is missing")
        elif not legacy.is_file():
            problems.append(f"{text_id}: cached-name audio alias is missing")
        elif hashlib.sha256(current.read_bytes()).digest() != hashlib.sha256(legacy.read_bytes()).digest():
            problems.append(f"{text_id}: cached-name alias still has old audio")

    source = (ROOT / "assets" / "offline-preloader.js").read_text()
    marker = "  var INLINE = "
    end_marker = ";\n  var BASE_DIR"
    start = source.index(marker) + len(marker)
    end = source.index(end_marker, start)
    inline = json.loads(source[start:end])
    if inline.get("./pg003_sec001.html") != html:
        problems.append("offline pg003 HTML is stale")
    if inline.get("./content/i18n/sw-TZ/texts.json") != texts:
        problems.append("offline texts.json is stale")
    if inline.get("./content/i18n/sw-TZ/audios.json") != audios:
        problems.append("offline audios.json is stale")

    if problems:
        raise SystemExit("\n".join(problems))
    print(
        f"AUDIT PASS: {len(TOC_ROWS)} Yaliyomo links match ADT navigation; "
        f"{len(target_ids)} Rehema clips are current and cache-compatible"
    )


if __name__ == "__main__":
    main()
