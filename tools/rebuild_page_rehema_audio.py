"""Replace every mapped clip on one page with Rehema Natural sw-TZ speech."""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/private/tmp/edge_tts_runtime")
import edge_tts

VOICE = "sw-TZ-RehemaNeural"
ORDINALS = {4: "nne", 5: "tano", 6: "sita", 7: "saba", 8: "nane", 9: "tisa", 10: "kumi", 11: "kumi na moja"}
ONES = {0: "", 1: "moja", 2: "mbili", 3: "tatu", 4: "nne", 5: "tano", 6: "sita", 7: "saba", 8: "nane", 9: "tisa"}
TENS = {10: "kumi", 20: "ishirini", 30: "thelathini", 40: "arobaini", 50: "hamsini", 60: "sitini", 70: "sabini", 80: "themanini", 90: "tisini"}


def swahili_number(number: int) -> str:
    if number < 10:
        return ONES[number]
    if number < 100:
        tens, ones = divmod(number, 10)
        base = TENS[tens * 10]
        return base if not ones else f"{base} na {ONES[ones]}"
    if number < 1000:
        hundreds, remainder = divmod(number, 100)
        base = f"mia {ONES[hundreds]}"
        return base if not remainder else f"{base} {swahili_number(remainder)}"
    thousands, remainder = divmod(number, 1000)
    base = f"elfu {ONES[thousands]}"
    return base if not remainder else f"{base} {swahili_number(remainder)}"


def speech_for(text: str, text_id: str) -> str:
    match = re.fullmatch(r"\s*(\d+)\.?\s*", text)
    if match and int(match.group(1)) in ORDINALS:
        return f"Swali la {ORDINALS[int(match.group(1))]}."
    speech = re.sub(
        r"^\s*\(([a-dA-D])\)\s*",
        lambda item: f"Kipengele {item.group(1).upper()}. ",
        text,
    )
    if text_id in {"pg047_n0007", "pg047_n0007_easy_read", "pg013_n0018", "pg013_n0018_easy_read", "pg013_n0019", "pg013_n0019_easy_read"}:
        speech = speech.replace("/", " au ")
    if text_id in {"pg023_n0015", "pg023_n0015_easy_read"}:
        speech = speech.replace("5,895", "elfu tano mia nane na tisini na tano")
    if text_id in {"pg024_n0002", "pg024_n0002_easy_read", "pg024_n0003", "pg024_n0003_easy_read"}:
        speech = re.sub(r"(?<!\d)(\d{1,3}),\s*(\d{3})(?!\d)",
                        lambda item: swahili_number(int(item.group(1) + item.group(2))), speech)
    return speech


async def render(text_id, speech, destination, limiter):
    for attempt in range(1, 5):
        try:
            async with limiter:
                await edge_tts.Communicate(speech_for(speech, text_id), VOICE).save(str(destination))
            return text_id, None
        except Exception as error:
            if attempt == 4:
                return text_id, str(error)
            await asyncio.sleep(attempt)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--page", required=True, help="Page prefix, e.g. pg050")
    args = parser.parse_args()
    language = Path(args.root) / "content" / "i18n" / "sw-TZ"
    texts = json.loads((language / "texts.json").read_text())
    audios = json.loads((language / "audios.json").read_text())
    clips = [(text_id, text, language / "audio" / audios[text_id])
             for text_id, text in texts.items()
             if text_id.startswith(f"{args.page}_") and text_id in audios]
    print(f"Generating {len(clips)} Rehema clips for {args.page}", flush=True)
    limiter = asyncio.Semaphore(6)
    results = await asyncio.gather(*(render(*clip, limiter) for clip in clips))
    failures = [result for result in results if result[1]]
    if failures:
        raise SystemExit("; ".join(f"{text_id}: {error}" for text_id, error in failures))


if __name__ == "__main__":
    asyncio.run(main())
