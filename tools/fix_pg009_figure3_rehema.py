"""Correct pg009 Figure 3 image descriptions and replace their Rehema audio."""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "/private/tmp/edge_tts_runtime")
import edge_tts


ROOT = Path(__file__).resolve().parents[1]
LANGUAGE = ROOT / "content" / "i18n" / "sw-TZ"
VOICE = "sw-TZ-RehemaNeural"
TARGET_IDS = tuple(f"pg009_im{number:03d}" for number in range(1, 7))
VERSION = "rehema_figure3_v2"


async def render(text_id: str, speech: str, destination: Path) -> None:
    temporary = destination.with_name(f"{destination.stem}.tmp{destination.suffix}")
    try:
        await edge_tts.Communicate(speech, VOICE).save(str(temporary))
        if temporary.stat().st_size < 512:
            raise RuntimeError(f"TTS returned an empty clip for {text_id}")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


async def main() -> None:
    texts_path = LANGUAGE / "texts.json"
    audios_path = LANGUAGE / "audios.json"
    audio_dir = LANGUAGE / "audio"
    texts = json.loads(texts_path.read_text())
    audios = json.loads(audios_path.read_text())

    replacements: dict[str, str] = {}
    old_names: dict[str, str] = {}
    new_names: dict[str, str] = {}
    for text_id in TARGET_IDS:
        old_text = texts[text_id]
        new_text, count = re.subn(
            r"^Picha katika kielelezo namba 2\b",
            "Picha katika kielelezo namba 3",
            old_text,
            count=1,
            flags=re.IGNORECASE,
        )
        if count != 1:
            raise SystemExit(f"Unexpected source description for {text_id}: {old_text}")
        replacements[text_id] = new_text
        old_names[text_id] = audios[text_id]
        new_names[text_id] = f"{text_id}_{VERSION}.mp3"

    await asyncio.gather(*(
        render(text_id, replacements[text_id], audio_dir / new_names[text_id])
        for text_id in TARGET_IDS
    ))

    preloader_path = ROOT / "assets" / "offline-preloader.js"
    preloader = preloader_path.read_text()
    for text_id in TARGET_IDS:
        old_text = texts[text_id]
        old_name = old_names[text_id]
        if old_text not in preloader:
            raise SystemExit(f"Missing offline description for {text_id}")
        old_mapping = f'"{text_id}":"{old_name}"'
        if old_mapping not in preloader:
            raise SystemExit(f"Missing offline audio mapping for {text_id}")
        preloader = preloader.replace(old_text, replacements[text_id], 1)
        preloader = preloader.replace(
            old_mapping, f'"{text_id}":"{new_names[text_id]}"', 1
        )
        texts[text_id] = replacements[text_id]
        audios[text_id] = new_names[text_id]

    texts_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n")
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n")
    preloader_path.write_text(preloader)

    # Keep legacy filenames as byte-identical aliases of the corrected Rehema
    # clips. Browsers with a cached audios.json can otherwise pause on a 404.
    for text_id in TARGET_IDS:
        current = audio_dir / new_names[text_id]
        for legacy_name in (
            f"{text_id}_rehema_image_v1.mp3",
            f"{text_id}_male.mp3",
        ):
            shutil.copyfile(current, audio_dir / legacy_name)

    print(
        f"Generated {len(TARGET_IDS)} new {VOICE} clips for pg009 Figure 3"
    )


if __name__ == "__main__":
    asyncio.run(main())
