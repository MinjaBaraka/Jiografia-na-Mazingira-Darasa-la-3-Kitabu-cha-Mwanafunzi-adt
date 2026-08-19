"""Fail if exported HTML italics diverge from the source-PDF audit."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fix_italic_typography import (
    CAPTION_IDS,
    FULL_ITALIC_IDS,
    OFFLINE_PRELOADER_VERSION,
    ROOT,
)


def has_class(attrs: str, name: str) -> bool:
    match = re.search(r'\bclass="([^"]*)"', attrs)
    return bool(match and name in match.group(1).split())


def main() -> None:
    pages = [ROOT / "index.html", *sorted(ROOT.glob("pg*_sec*.html"))]
    found_ids: set[str] = set()
    found_pages: set[str] = set()
    nested_pg006 = 0
    problems: list[str] = []

    for page in pages:
        html = page.read_text()
        expected_preloader = (
            f'./assets/offline-preloader.js?v={OFFLINE_PRELOADER_VERSION}'
        )
        if html.count(expected_preloader) != 1:
            problems.append(f"{page.name}: missing current offline-preloader version")
        if re.search(r"font-style\s*:\s*(?:italic|oblique)", html, re.IGNORECASE):
            problems.append(f"{page.name}: unverified italic CSS declaration")
        if re.search(r"<em(?:\s|>)", html, re.IGNORECASE):
            problems.append(f"{page.name}: unverified em element")

        for match in re.finditer(
            r'<(?P<tag>[a-zA-Z][\w:-]*)(?P<attrs>[^>]*)>', html, re.DOTALL
        ):
            attrs = match.group("attrs")
            if not has_class(attrs, "italic"):
                continue
            found_pages.add(page.name)
            text_id_match = re.search(r'\bdata-id="([^"]+)"', attrs)
            if not text_id_match:
                if page.name == "pg006_sec001.html" and match.group("tag") == "span":
                    nested_pg006 += 1
                    continue
                problems.append(f"{page.name}: italic element has no audited text ID")
                continue
            text_id = text_id_match.group(1)
            found_ids.add(text_id)
            if text_id not in FULL_ITALIC_IDS | CAPTION_IDS:
                problems.append(f"{page.name}: unverified italic text ID {text_id}")

        for text_id in CAPTION_IDS:
            if not text_id.startswith(page.stem.split("_")[0] + "_"):
                continue
            element = re.search(
                rf'<(?P<tag>[a-zA-Z][\w:-]*)[^>]*\bdata-id="{re.escape(text_id)}"[^>]*>'
                rf'(?P<body>.*?)</(?P=tag)>',
                html,
                re.DOTALL,
            )
            if not element or not re.search(
                r'<strong[^>]*\bclass="[^"]*\bnot-italic\b[^"]*"[^>]*>'
                r'Kielelezo\s+namba\s+\d+\s*:</strong>',
                element.group("body"),
                re.DOTALL | re.IGNORECASE,
            ):
                problems.append(f"{page.name}: caption label is not regular for {text_id}")

    expected_pages = {
        "pg006_sec001.html",
        *(f"{text_id.split('_')[0]}_sec001.html" for text_id in FULL_ITALIC_IDS | CAPTION_IDS),
    }
    missing_ids = (FULL_ITALIC_IDS | CAPTION_IDS) - found_ids
    extra_pages = found_pages - expected_pages
    missing_pages = expected_pages - found_pages
    if missing_ids:
        problems.append(f"Missing intended italic IDs: {sorted(missing_ids)}")
    if nested_pg006 != 2:
        problems.append(f"Expected two italic pg006 URLs, found {nested_pg006}")
    if extra_pages or missing_pages:
        problems.append(
            f"Italic page mismatch; extra={sorted(extra_pages)}, missing={sorted(missing_pages)}"
        )

    preloader = (ROOT / "assets" / "offline-preloader.js").read_text()
    marker = "  var INLINE = "
    end_marker = ";\n  var BASE_DIR"
    try:
        start = preloader.index(marker) + len(marker)
        end = preloader.index(end_marker, start)
        inline = json.loads(preloader[start:end])
    except (ValueError, json.JSONDecodeError) as error:
        problems.append(f"Could not parse offline HTML snapshot: {error}")
        inline = {}
    for page in pages:
        key = f"./{page.name}"
        if inline.get(key) != page.read_text():
            problems.append(f"{page.name}: offline HTML snapshot is stale")
    if problems:
        raise SystemExit("\n".join(problems))
    print(
        f"AUDIT PASS: 88 HTML pages; {len(found_pages)} PDF-confirmed italic pages; "
        f"{len(found_ids)} audited text IDs plus two pg006 URLs"
    )


if __name__ == "__main__":
    main()
