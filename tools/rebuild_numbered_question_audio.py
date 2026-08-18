"""Regenerate Rehema clips so numbered questions are spoken as ordinals."""

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/private/tmp/edge_tts_runtime")
import edge_tts

VOICE = "sw-TZ-RehemaNeural"
ORDINALS = {
    1: "kwanza", 2: "pili", 3: "tatu", 4: "nne", 5: "tano",
    6: "sita", 7: "saba", 8: "nane", 9: "tisa", 10: "kumi",
    11: "kumi na moja", 12: "kumi na mbili", 13: "kumi na tatu",
}


def spoken_question(text: str) -> str | None:
    match = re.match(r"^\s*(\d+)\.\s*(.*)$", text)
    if not match:
        return None
    number = int(match.group(1))
    ordinal = ORDINALS.get(number)
    if not ordinal:
        return None
    remainder = match.group(2).strip()
    return f"Swali la {ordinal}." + (f" {remainder}" if remainder else "")


async def render(text_id: str, speech: str, path: Path, limiter: asyncio.Semaphore):
    for attempt in range(1, 5):
        try:
            async with limiter:
                await edge_tts.Communicate(speech, VOICE).save(str(path))
            return text_id, None
        except Exception as error:
            if attempt == 4:
                return text_id, str(error)
            await asyncio.sleep(attempt)


async def main():
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(".")
    language = root / "content" / "i18n" / "sw-TZ"
    texts = json.loads((language / "texts.json").read_text())
    audios = json.loads((language / "audios.json").read_text())
    clips = {
        text_id: speech
        for text_id, text in texts.items()
        if (speech := spoken_question(text))
        and audios.get(text_id) == f"{text_id}_rehema.mp3"
    }
    print(f"Generating {len(clips)} numbered Rehema question clips", flush=True)
    limiter = asyncio.Semaphore(6)
    output = language / "audio"
    jobs = [render(text_id, speech, output / f"{text_id}_rehema.mp3", limiter)
            for text_id, speech in clips.items()]
    failures = [result for result in await asyncio.gather(*jobs) if result[1]]
    if failures:
        raise SystemExit("; ".join(f"{text_id}: {error}" for text_id, error in failures))


if __name__ == "__main__":
    asyncio.run(main())
