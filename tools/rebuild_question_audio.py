import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, "/private/tmp/edge_tts_runtime")
import edge_tts

VOICE = "sw-TZ-RehemaNeural"


async def build_clip(text_id, speech, destination, limiter):
    for attempt in range(1, 5):
        try:
            async with limiter:
                await edge_tts.Communicate(speech, VOICE).save(str(destination))
            return text_id, ""
        except Exception as error:
            if attempt == 4:
                return text_id, str(error)
            await asyncio.sleep(attempt)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--overrides", required=True)
    parser.add_argument("--concurrency", type=int, default=6)
    args = parser.parse_args()

    root = Path(args.root)
    language_dir = root / "content" / "i18n" / "sw-TZ"
    audios = json.loads((language_dir / "audios.json").read_text())
    overrides = json.loads(Path(args.overrides).read_text())
    unknown = set(overrides).difference(audios)
    if unknown:
        raise SystemExit(f"Unknown audio IDs: {', '.join(sorted(unknown))}")

    print(f"Generating {len(overrides)} Rehema question clips", flush=True)
    output_dir = language_dir / "audio"
    limiter = asyncio.Semaphore(args.concurrency)
    jobs = [
        build_clip(text_id, speech, output_dir / f"{text_id}_rehema.mp3", limiter)
        for text_id, speech in overrides.items()
    ]
    failures = []
    for job in asyncio.as_completed(jobs):
        text_id, error = await job
        if error:
            failures.append((text_id, error))
    if failures:
        raise SystemExit("; ".join(f"{text_id}: {error}" for text_id, error in failures))


if __name__ == "__main__":
    asyncio.run(main())
