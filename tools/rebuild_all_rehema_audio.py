"""Replace every non-empty mapped audio clip with Rehema Natural (sw-TZ)."""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/private/tmp/edge_tts_runtime")
import edge_tts

from rehema_speech import normalize_global_narration


VOICE = "sw-TZ-RehemaNeural"
ORDINALS = {
    1: "kwanza", 2: "pili", 3: "tatu", 4: "nne", 5: "tano",
    6: "sita", 7: "saba", 8: "nane", 9: "tisa", 10: "kumi",
    11: "kumi na moja", 12: "kumi na mbili", 13: "kumi na tatu",
}


def speech_for(text: str, text_id: str = "") -> str:
    """Make numbered prompts sound natural for a primary-school learner."""
    speech = re.sub(r"\s*/\s*", " au ", text.strip())
    speech = normalize_global_narration(speech, text_id)
    match = re.match(r"^\s*(\d+)\.\s*(.+)$", speech, flags=re.DOTALL)
    if match and (ordinal := ORDINALS.get(int(match.group(1)))):
        return f"Swali la {ordinal}. {match.group(2).strip()}"
    return re.sub(
        r"^\(([a-dA-D])\)\s*",
        lambda item: f"Kipengele {item.group(1).upper()}. ",
        speech,
    )


async def render(text_id: str, speech: str, destination: Path, limiter: asyncio.Semaphore):
    temporary = destination.with_name(f"{destination.stem}.tmp{destination.suffix}")
    for attempt in range(1, 5):
        try:
            async with limiter:
                await edge_tts.Communicate(speech, VOICE).save(str(temporary))
            if temporary.stat().st_size < 512:
                raise RuntimeError("TTS returned an empty audio file")
            temporary.replace(destination)
            return text_id, None
        except Exception as error:
            temporary.unlink(missing_ok=True)
            if attempt == 4:
                return text_id, str(error)
            await asyncio.sleep(attempt)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--only", nargs="*", help="Optional text IDs to regenerate")
    parser.add_argument("--lettered", action="store_true", help="Regenerate (a) through (d) option clips")
    args = parser.parse_args()

    language = Path(args.root) / "content" / "i18n" / "sw-TZ"
    texts = json.loads((language / "texts.json").read_text())
    audios = json.loads((language / "audios.json").read_text())
    audio_dir = language / "audio"
    requested = set(args.only or audios)
    if args.lettered:
        requested = {
            text_id for text_id in requested
            if re.match(r"^\s*\([a-dA-D]\)\s*", texts.get(text_id, ""))
        }
    unknown = requested.difference(audios)
    if unknown:
        raise SystemExit(f"Unknown audio IDs: {', '.join(sorted(unknown))}")
    clips = [
        (text_id, speech_for(texts[text_id], text_id), audio_dir / filename)
        for text_id, filename in audios.items()
        if text_id in requested and texts.get(text_id, "").strip()
    ]
    empty = len(audios) - len(clips)
    print(f"Generating {len(clips)} Rehema clips; retaining {empty} empty-text mappings", flush=True)
    limiter = asyncio.Semaphore(args.concurrency)
    results = await asyncio.gather(*(render(*clip, limiter) for clip in clips))
    failures = [result for result in results if result[1]]
    if failures:
        failed = "; ".join(f"{text_id}: {error}" for text_id, error in failures)
        raise SystemExit(failed)


if __name__ == "__main__":
    asyncio.run(main())
