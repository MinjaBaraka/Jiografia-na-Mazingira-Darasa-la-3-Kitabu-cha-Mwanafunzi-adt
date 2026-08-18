"""Render pg004 credits with slow, clear Rehema narration."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, "/private/tmp/edge_tts_runtime")
import edge_tts


VOICE = "sw-TZ-RehemaNeural"
RATE = "-28%"
SPEECH = {
    "pg004_n0010": "Waandishi...",
    "pg004_n0012": "Bi. Blandina F. Ajali... Bw. Karani H. Mdee... na Bi. Selestina C. Lwanga.",
    "pg004_n0015": "Wahariri...",
    "pg004_n0017": "Dkt. Christopher M. William... Dkt. Mromba C. Mikidadi... Dkt. Johnstone M. Andrea... Dkt. Lydia A. Kimaryo... Bi. Ndimbumi J. Mboneke... na Bi. Dalia C. Kilamlya.",
    "pg004_n0020": "Wasanifu...",
    "pg004_n0022": "Bw. Maulid M. Ramadhani.",
    "pg004_n0025": "Wachoraji...",
    "pg004_n0027": "Bw. Fikiri A. Msimbe... na Yohana P. Mwenda.",
    "pg004_n0030": "Mratibu...",
    "pg004_n0032": "Bi. Blandina F. Ajali.",
}
SPEECH.update({f"{text_id}_easy_read": speech for text_id, speech in list(SPEECH.items())})


async def render(text_id: str, speech: str, path: Path, limiter: asyncio.Semaphore):
    for attempt in range(1, 5):
        try:
            async with limiter:
                await edge_tts.Communicate(speech, VOICE, rate=RATE).save(str(path))
            if path.stat().st_size < 512:
                raise RuntimeError("TTS returned an empty audio file")
            return text_id, None
        except Exception as error:
            if attempt == 4:
                return text_id, str(error)
            await asyncio.sleep(attempt)


async def main():
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(".")
    language = root / "content" / "i18n" / "sw-TZ"
    audios = json.loads((language / "audios.json").read_text())
    unknown = set(SPEECH).difference(audios)
    if unknown:
        raise SystemExit(f"Unknown audio IDs: {', '.join(sorted(unknown))}")
    limiter = asyncio.Semaphore(3)
    clips = [
        render(text_id, speech, language / "audio" / audios[text_id], limiter)
        for text_id, speech in SPEECH.items()
    ]
    print(f"Generating {len(clips)} slow, clear Rehema credit clips", flush=True)
    failures = [result for result in await asyncio.gather(*clips) if result[1]]
    if failures:
        raise SystemExit("; ".join(f"{text_id}: {error}" for text_id, error in failures))


if __name__ == "__main__":
    asyncio.run(main())
