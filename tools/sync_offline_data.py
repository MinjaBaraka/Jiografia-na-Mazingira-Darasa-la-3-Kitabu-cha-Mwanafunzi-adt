"""Synchronize JSON data used by the file:// offline preloader."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRELOADER = ROOT / "assets" / "offline-preloader.js"
INLINE_MARKER = "  var INLINE = "
END_MARKER = ";\n  var BASE_DIR"
DATA_FILES = [
    ROOT / "assets" / "config.json",
    ROOT / "content" / "pages.json",
    ROOT / "content" / "toc.json",
    *sorted((ROOT / "content" / "i18n").rglob("*.json")),
]


def main() -> None:
    source = PRELOADER.read_text()
    start = source.index(INLINE_MARKER) + len(INLINE_MARKER)
    end = source.index(END_MARKER, start)
    inline = json.loads(source[start:end])

    for path in DATA_FILES:
        inline[f"./{path.relative_to(ROOT)}"] = json.loads(path.read_text())

    serialized = json.dumps(inline, ensure_ascii=False, separators=(",", ":"))
    PRELOADER.write_text(source[:start] + serialized + source[end:])
    print(f"Synchronized {len(DATA_FILES)} JSON files into the offline preloader")


if __name__ == "__main__":
    main()
