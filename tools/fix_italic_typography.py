"""Synchronize exported HTML italics with the embedded typography in the PDF."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OFFLINE_PRELOADER_VERSION = "italic-audit-v1"

# Complete elements whose text is italic in the source PDF.
FULL_ITALIC_IDS = {
    "pg007_n0007", "pg007_n0008", "pg007_n0009", "pg007_n0010",
    "pg014_n0030",
    "pg020_n0007", "pg020_n0008", "pg020_n0009", "pg020_n0010", "pg020_n0011",
    "pg025_n0002",
    "pg028_n0002", "pg028_n0012",
    "pg029_n0005",
    "pg030_n0004",
    "pg034_n0008", "pg034_n0009", "pg034_n0010", "pg034_n0011", "pg034_n0012",
    "pg052_n0010", "pg052_n0011", "pg052_n0012", "pg052_n0013", "pg052_n0014",
    "pg088_n0005", "pg088_n0009", "pg088_n0013", "pg088_n0017",
    "pg088_n0018", "pg088_n0021", "pg088_n0025", "pg088_n0029", "pg088_n0033",
}

# In figure captions the label is regular/bold while the description is italic.
CAPTION_IDS = {
    "pg008_n0009", "pg009_n0009", "pg009_n0028", "pg011_n0007",
    "pg012_n0011", "pg021_n0007", "pg022_n0015", "pg023_n0021",
    "pg024_n0015", "pg025_n0013", "pg027_n0007", "pg030_n0002",
    "pg030_n0009", "pg037_n0024", "pg039_n0014", "pg041_n0007",
    "pg043_n0007", "pg046_n0002", "pg054_n0002", "pg055_n0009",
    "pg056_n0011", "pg058_n0002", "pg059_n0011", "pg060_n0011",
    "pg063_n0010", "pg066_n0010", "pg069_n0009", "pg072_n0011",
    "pg075_n0005", "pg076_n0012", "pg078_n0020", "pg080_n0011",
}


def update_class_attribute(
    attrs: str, add: set[str] = set(), remove: set[str] = set()
) -> str:
    match = re.search(r'\bclass="([^"]*)"', attrs)
    if match:
        classes = [
            item for item in match.group(1).split()
            if item != "italic" and item not in remove
        ]
        for item in sorted(add):
            if item not in classes:
                classes.append(item)
        return attrs[:match.start(1)] + " ".join(classes) + attrs[match.end(1):]
    if add:
        return attrs + f' class="{" ".join(sorted(add))}"'
    return attrs


def strip_unverified_italics(html: str) -> str:
    html = re.sub(
        r'class="([^"]*)"',
        lambda match: 'class="' + " ".join(
            item for item in match.group(1).split()
            if item not in {"italic", "not-italic"}
            and not item.endswith(":not-italic")
        ) + '"',
        html,
    )
    html = re.sub(
        r"font-style\s*:\s*(?:italic|oblique)",
        "font-style: normal",
        html,
        flags=re.IGNORECASE,
    )
    return re.sub(
        r"\./assets/offline-preloader\.js(?:\?v=[^\"]*)?",
        f"./assets/offline-preloader.js?v={OFFLINE_PRELOADER_VERSION}",
        html,
    )


def add_class_to_id(
    html: str, text_id: str, class_name: str, remove: set[str] = set()
) -> str:
    pattern = re.compile(
        rf'<(?P<tag>[a-zA-Z][\w:-]*)(?P<attrs>[^>]*\bdata-id="{re.escape(text_id)}"[^>]*)>',
        flags=re.DOTALL,
    )
    matches = list(pattern.finditer(html))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one HTML element for {text_id}, found {len(matches)}")
    match = matches[0]
    attrs = update_class_attribute(match.group("attrs"), {class_name}, remove)
    replacement = f'<{match.group("tag")}{attrs}>'
    return html[:match.start()] + replacement + html[match.end():]


def style_caption(html: str, text_id: str) -> str:
    html = add_class_to_id(html, text_id, "italic", {"not-italic"})
    element = re.compile(
        rf'(<(?P<tag>[a-zA-Z][\w:-]*)[^>]*\bdata-id="{re.escape(text_id)}"[^>]*>)(?P<body>.*?)(</(?P=tag)>)',
        flags=re.DOTALL,
    )
    match = element.search(html)
    if not match:
        raise RuntimeError(f"Could not read caption element {text_id}")
    body = match.group("body")
    strong = re.search(r'<strong(?P<attrs>[^>]*)>(?P<label>.*?)</strong>', body, flags=re.DOTALL)
    if strong:
        attrs = update_class_attribute(strong.group("attrs"), {"not-italic"})
        new_strong = f'<strong{attrs}>{strong.group("label")}</strong>'
        body = body[:strong.start()] + new_strong + body[strong.end():]
    else:
        label = re.search(r'Kielelezo\s+namba\s+(\d+)\s*:', body, flags=re.IGNORECASE)
        if not label:
            raise RuntimeError(f"Caption {text_id} has no Kielelezo label")
        number = label.group(1)
        replacement = f'<strong class="not-italic">Kielelezo namba {number}:</strong>'
        body = body[:label.start()] + replacement + body[label.end():]
    return html[:match.start("body")] + body + html[match.end("body"):]


def style_pg006_urls(html: str) -> str:
    region = re.compile(
        r'<span\s+data-id="pg006_n0013"[^>]*>.*?'
        r'<br><span\s+data-id="pg006_n0014"[^>]*>.*?</span></p>',
        flags=re.DOTALL,
    )
    replacement = (
        '<span data-id="pg006_n0013">Jifunze zaidi kupitia Maktaba Mtandao '
        '<span class="italic">https://ol.tie.go.tz</span></span><br>'
        '<span data-id="pg006_n0014">au <span class="italic">ol.tie.go.tz</span></span></p>'
    )
    html, count = region.subn(replacement, html, count=1)
    if count != 1:
        raise RuntimeError("Could not style both pg006 source URLs")
    return html


def style_pg088_edition(html: str) -> str:
    pattern = re.compile(
        r'<span\s+data-id="pg088_n0013"[^>]*>.*?'
        r'(?=<span\s+data-id="pg088_n0014")',
        flags=re.DOTALL,
    )
    replacement = (
        '<span data-id="pg088_n0013" class="italic">Republic of Kenya upper '
        'primary level designs subject social studies grade 6 '
        '<span class="not-italic">(1st ed.).</span></span>\n                '
    )
    html, count = pattern.subn(replacement, html, count=1)
    if count != 1:
        raise RuntimeError("Could not preserve the regular pg088 edition text")
    return html


def main() -> None:
    pages = [ROOT / "index.html", *sorted(ROOT.glob("pg*_sec*.html"))]
    changed = 0
    seen_full: set[str] = set()
    seen_captions: set[str] = set()
    for page in pages:
        html = strip_unverified_italics(page.read_text())
        page_prefix = page.stem.split("_")[0] + "_"
        for text_id in sorted(item for item in FULL_ITALIC_IDS if item.startswith(page_prefix)):
            html = add_class_to_id(html, text_id, "italic")
            seen_full.add(text_id)
        for text_id in sorted(item for item in CAPTION_IDS if item.startswith(page_prefix)):
            html = style_caption(html, text_id)
            seen_captions.add(text_id)
        if page.name == "pg006_sec001.html":
            html = style_pg006_urls(html)
        if page.name == "pg088_sec001.html":
            html = style_pg088_edition(html)
        original = page.read_text()
        if html != original:
            page.write_text(html)
            changed += 1

    missing_full = FULL_ITALIC_IDS - seen_full
    missing_captions = CAPTION_IDS - seen_captions
    if missing_full or missing_captions:
        raise SystemExit(f"Missing IDs: {sorted(missing_full | missing_captions)}")
    print(f"Corrected italic typography in {changed} of {len(pages)} HTML pages")


if __name__ == "__main__":
    main()
