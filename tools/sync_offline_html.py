"""Synchronize exported page HTML into the generated offline preloader."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRELOADER = ROOT / "assets" / "offline-preloader.js"
INLINE_MARKER = "  var INLINE = "
END_MARKER = ";\n  var BASE_DIR"


def main() -> None:
    source = PRELOADER.read_text()
    start = source.index(INLINE_MARKER) + len(INLINE_MARKER)
    end = source.index(END_MARKER, start)
    inline = json.loads(source[start:end])

    pages = [
        ROOT / "index.html",
        *sorted(ROOT.glob("pg*_sec*.html")),
        ROOT / "back_cover_sec001.html",
    ]
    for page in pages:
        inline[f"./{page.name}"] = page.read_text()

    serialized = json.dumps(inline, ensure_ascii=False, separators=(",", ":"))
    updated = source[:start] + serialized + source[end:]
    if updated != source:
        PRELOADER.write_text(updated)
    print(f"Synchronized {len(pages)} HTML pages into the offline preloader")


if __name__ == "__main__":
    main()
