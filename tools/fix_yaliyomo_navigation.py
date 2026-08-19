"""Align Yaliyomo numbers/links with ADT navigation and rebuild Rehema audio."""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "/private/tmp/edge_tts_runtime")
import edge_tts


ROOT = Path(__file__).resolve().parents[1]
LANGUAGE = ROOT / "content" / "i18n" / "sw-TZ"
VOICE = "sw-TZ-RehemaNeural"
VERSION = "rehema_toc_v2"

TOC_ROWS = (
    ("pg003_n0005", "pg003_n0006", "Shukurani", 4, "pg004_sec001.html"),
    ("pg003_n0008", "pg003_n0009", "Utangulizi", 6, "pg006_sec001.html"),
    ("pg003_n0011", "pg003_n0012", "Sura ya Kwanza", 7, "pg007_sec001.html"),
    ("pg003_n0014", "pg003_n0015", "Dhana ya Jiografia na Mazingira", 7, "pg007_sec001.html"),
    ("pg003_n0017", "pg003_n0018", "Sura ya Pili", 20, "pg020_sec001.html"),
    ("pg003_n0020", "pg003_n0021", "Sura ya nchi.", 20, "pg020_sec001.html"),
    ("pg003_n0023", "pg003_n0024", "Sura ya Tatu", 34, "pg034_sec001.html"),
    ("pg003_n0026", "pg003_n0027", "Utunzaji wa mazingira", 34, "pg034_sec001.html"),
    ("pg003_n0029", "pg003_n0030", "Sura ya Nne", 52, "pg052_sec001.html"),
    ("pg003_n0032", "pg003_n0033", "Uharibifu wa mazingira", 52, "pg052_sec001.html"),
    ("pg003_n0035", "pg003_n0036", "Jaribio", 85, "pg085_sec001.html"),
    ("pg003_n0038", "pg003_n0039", "Marejeleo", 88, "pg088_sec001.html"),
)

NUMBER_WORDS = {
    4: "nne",
    6: "sita",
    7: "saba",
    20: "ishirini",
    34: "thelathini na nne",
    52: "hamsini na mbili",
    85: "themanini na tano",
    88: "themanini na nane",
}


def speech_for(text_id: str, text: str) -> str:
    number_ids = {row[1]: row[3] for row in TOC_ROWS}
    base_id = text_id.removesuffix("_easy_read")
    if base_id in number_ids:
        return f"Ukurasa wa {NUMBER_WORDS[number_ids[base_id]]}."
    return text


async def render(text_id: str, speech: str, destination: Path, limiter: asyncio.Semaphore) -> None:
    temporary = destination.with_name(f"{destination.stem}.tmp{destination.suffix}")
    for attempt in range(1, 5):
        try:
            temporary.unlink(missing_ok=True)
            async with limiter:
                await edge_tts.Communicate(speech, VOICE).save(str(temporary))
            if temporary.stat().st_size < 512:
                raise RuntimeError(f"TTS returned an empty clip for {text_id}")
            temporary.replace(destination)
            return
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == 4:
                raise
            await asyncio.sleep(attempt)


async def main() -> None:
    texts_path = LANGUAGE / "texts.json"
    audios_path = LANGUAGE / "audios.json"
    audio_dir = LANGUAGE / "audio"
    texts = json.loads(texts_path.read_text())
    audios = json.loads(audios_path.read_text())

    for _, number_id, _, page_number, _ in TOC_ROWS:
        texts[number_id] = str(page_number)
        texts[f"{number_id}_easy_read"] = str(page_number)

    target_ids = [
        text_id for text_id in texts
        if text_id.startswith("pg003_") and text_id in audios
    ]
    old_names = {text_id: audios[text_id] for text_id in target_ids}
    new_names = {
        text_id: f"{text_id}_{VERSION}.mp3" for text_id in target_ids
    }

    pending = [
        text_id for text_id in target_ids
        if not (audio_dir / new_names[text_id]).is_file()
        or (audio_dir / new_names[text_id]).stat().st_size < 512
    ]
    for temporary in audio_dir.glob("pg003_*_rehema_toc_v2.tmp.mp3"):
        temporary.unlink()
    print(
        f"Generating {len(pending)} remaining {VOICE} Yaliyomo clips",
        flush=True,
    )
    limiter = asyncio.Semaphore(12)
    await asyncio.gather(*(
        render(
            text_id,
            speech_for(text_id, texts[text_id]),
            audio_dir / new_names[text_id],
            limiter,
        )
        for text_id in pending
    ))

    for text_id in target_ids:
        corrected = audio_dir / new_names[text_id]
        old_name = old_names[text_id]
        if old_name != new_names[text_id]:
            shutil.copyfile(corrected, audio_dir / old_name)
        audios[text_id] = new_names[text_id]

    texts_path.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n")
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n")

    preloader_path = ROOT / "assets" / "offline-preloader.js"
    source = preloader_path.read_text()
    marker = "  var INLINE = "
    end_marker = ";\n  var BASE_DIR"
    start = source.index(marker) + len(marker)
    end = source.index(end_marker, start)
    inline = json.loads(source[start:end])
    inline["./content/i18n/sw-TZ/texts.json"] = texts
    inline["./content/i18n/sw-TZ/audios.json"] = audios
    serialized = json.dumps(inline, ensure_ascii=False, separators=(",", ":"))
    preloader_path.write_text(source[:start] + serialized + source[end:])

    print(f"Generated {len(target_ids)} new {VOICE} Yaliyomo clips")


if __name__ == "__main__":
    asyncio.run(main())
