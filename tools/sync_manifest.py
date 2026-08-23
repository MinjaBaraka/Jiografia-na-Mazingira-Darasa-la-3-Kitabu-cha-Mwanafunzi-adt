"""Synchronize the SCORM manifest with the current ADT spine and resources."""

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "imsmanifest.xml"
RESOURCE_ROOTS = (ROOT / "assets", ROOT / "content", ROOT / "images")


def exported_resources() -> list[str]:
    pages = json.loads((ROOT / "content" / "pages.json").read_text())
    hrefs = [entry["href"] for entry in pages]
    missing = [href for href in hrefs if not (ROOT / href).is_file()]
    if missing:
        raise FileNotFoundError(f"Spine resources are missing: {missing}")

    resources = {"cover.png", *hrefs}
    for directory in RESOURCE_ROOTS:
        resources.update(
            path.relative_to(ROOT).as_posix()
            for path in directory.rglob("*")
            if path.is_file() and path.name != ".DS_Store"
        )
    return sorted(resources)


def main() -> None:
    config = json.loads((ROOT / "assets" / "config.json").read_text())
    pages = json.loads((ROOT / "content" / "pages.json").read_text())
    if not pages:
        raise ValueError("The ADT spine is empty")

    title = html.escape(str(config.get("title", "Accessible Digital Textbook")))
    launch = html.escape(pages[0]["href"], quote=True)
    files = "\n".join(
        f'      <file href="{html.escape(path, quote=True)}"/>'
        for path in exported_resources()
    )
    manifest = f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="ADT_EXPORT" version="1.0"
  xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd
                       http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="ADT_ORG">
    <organization identifier="ADT_ORG">
      <title>{title}</title>
      <item identifier="ITEM_1" identifierref="RESOURCE_1">
        <title>{title}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RESOURCE_1" type="webcontent"
              adlcp:scormtype="sco" href="{launch}">
{files}
    </resource>
  </resources>
</manifest>
'''
    MANIFEST.write_text(manifest)
    print(f"Synchronized {len(exported_resources())} files into the SCORM manifest")


if __name__ == "__main__":
    main()
