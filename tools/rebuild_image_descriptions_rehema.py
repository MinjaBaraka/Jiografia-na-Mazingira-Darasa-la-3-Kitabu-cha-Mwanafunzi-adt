"""Rewrite accessible image descriptions and replace their audio with Rehema."""

import asyncio
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "/private/tmp/edge_tts_runtime")
import edge_tts

VOICE = "sw-TZ-RehemaNeural"


def figure_number(texts: dict, image_id: str) -> str | None:
    page = image_id[:5]
    special = {
        "pg009_im007": "2",
        "pg030_im001": "8",
        "pg030_im002": "9",
    }
    if image_id in special:
        return special[image_id]
    numbers = []
    for key, value in texts.items():
        if key.startswith(f"{page}_") and not key.endswith("_easy_read"):
            numbers.extend(re.findall(r"Kielelezo namba\s+(\d+)", value, flags=re.I))
    return numbers[0] if numbers else None


def description(texts: dict, image_id: str, old: str) -> str:
    number = figure_number(texts, image_id)
    cleaned = re.sub(r"^Kielelezo namba\s+\d+\s+(?:kinaonyesha|kinawasilisha)\s*", "", old, flags=re.I)
    cleaned = re.sub(r"^Kielelezo cha\s+", "", cleaned, flags=re.I)
    cleaned = cleaned[:1].lower() + cleaned[1:] if cleaned else cleaned
    if number:
        return f"Picha katika kielelezo namba {number} inaonesha {cleaned}"
    page = str(int(image_id[2:5]))
    return f"Picha kwenye ukurasa wa {page} inaonesha {cleaned}"


async def render(image_id: str, text: str, destination: Path, limiter: asyncio.Semaphore):
    for attempt in range(1, 5):
        try:
            async with limiter:
                await edge_tts.Communicate(text, VOICE).save(str(destination))
            return image_id, None
        except Exception as error:
            if attempt == 4:
                return image_id, str(error)
            await asyncio.sleep(attempt)


async def main():
    root = Path(__file__).resolve().parents[1]
    language = root / "content" / "i18n" / "sw-TZ"
    text_path = language / "texts.json"
    audio_path = language / "audios.json"
    texts = json.loads(text_path.read_text())
    audios = json.loads(audio_path.read_text())
    ids = [key for key in texts if re.fullmatch(r"pg\d{3}_im\d+", key)]
    replacements = {image_id: description(texts, image_id, texts[image_id]) for image_id in ids}
    audio_dir = language / "audio"
    clip_changes = []
    for image_id, new_text in replacements.items():
        if image_id not in audios:
            continue
        old_name = audios[image_id]
        old_path = audio_dir / old_name
        if not old_path.is_file():
            raise SystemExit(f"Missing mapped audio: {old_path}")
        new_name = f"{image_id}_rehema_image_v1.mp3"
        clip_changes.append((image_id, new_text, old_name, old_path, new_name, audio_dir / new_name))

    print(f"Updating {len(replacements)} descriptions and generating {len(clip_changes)} Rehema clips", flush=True)
    limiter = asyncio.Semaphore(6)
    results = await asyncio.gather(*(render(image_id, new_text, new_path, limiter)
                                   for image_id, new_text, _, _, _, new_path in clip_changes))
    failures = [result for result in results if result[1]]
    if failures:
        raise SystemExit("; ".join(f"{image_id}: {error}" for image_id, error in failures))

    preloader_path = root / "assets" / "offline-preloader.js"
    preloader = preloader_path.read_text()
    for image_id, new_text in replacements.items():
        old_text = texts[image_id]
        if old_text not in preloader:
            raise SystemExit(f"Missing cached description for {image_id}")
        preloader = preloader.replace(old_text, new_text)
        texts[image_id] = new_text
    for image_id, _, old_name, old_path, new_name, _ in clip_changes:
        old_entry = f'"{image_id}":"{old_name}"'
        if old_entry not in preloader:
            raise SystemExit(f"Missing cached audio mapping for {image_id}")
        preloader = preloader.replace(old_entry, f'"{image_id}":"{new_name}"', 1)
        audios[image_id] = new_name

    text_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n")
    audio_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n")
    preloader_path.write_text(preloader)
    for _, _, _, old_path, _, _ in clip_changes:
        old_path.unlink()


if __name__ == "__main__":
    asyncio.run(main())
