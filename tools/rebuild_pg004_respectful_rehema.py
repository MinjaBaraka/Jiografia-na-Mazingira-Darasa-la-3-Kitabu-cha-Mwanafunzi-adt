"""Render pg004 credits with deliberate, respectful Rehema narration."""

import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/private/tmp/edge_tts_runtime")
import edge_tts


VOICE = "sw-TZ-RehemaNeural"
RATE = "-5%"
NAME_PAUSE = 0.55
GROUP_PAUSE = 1.15
SEGMENTS = {
    "pg004_n0010": [("Waandishi.", GROUP_PAUSE)],
    "pg004_n0012": [("Bibi Blandina F. Ajali.", NAME_PAUSE), ("Bwana Karani H. Mdee.", NAME_PAUSE), ("Na Bibi Selestina C. Lwanga.", GROUP_PAUSE)],
    "pg004_n0015": [("Wahariri.", GROUP_PAUSE)],
    "pg004_n0017": [("Daktari Christopher M. William.", NAME_PAUSE), ("Daktari Mromba C. Mikidadi.", NAME_PAUSE), ("Daktari Johnstone M. Andrea.", NAME_PAUSE), ("Daktari Lydia A. Kimaryo.", NAME_PAUSE), ("Bibi Ndimbumi J. Mboneke.", NAME_PAUSE), ("Na Bibi Dalia C. Kilamlya.", GROUP_PAUSE)],
    "pg004_n0020": [("Wasanifu.", GROUP_PAUSE)],
    "pg004_n0022": [("Bwana Maulid M. Ramadhani.", GROUP_PAUSE)],
    "pg004_n0025": [("Wachoraji.", GROUP_PAUSE)],
    "pg004_n0027": [("Bwana Fikiri A. Msimbe.", NAME_PAUSE), ("Na Yohana P. Mwenda.", GROUP_PAUSE)],
    "pg004_n0030": [("Mratibu.", GROUP_PAUSE)],
    "pg004_n0032": [("Bibi Blandina F. Ajali.", 0)],
}
SEGMENTS.update({f"{text_id}_easy_read": segments for text_id, segments in list(SEGMENTS.items())})


async def tts(text, path, limiter):
    for attempt in range(1, 5):
        try:
            async with limiter:
                await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(path))
            if path.stat().st_size < 512:
                raise RuntimeError("TTS returned an empty audio file")
            return None
        except Exception as error:
            if attempt == 4:
                return str(error)
            await asyncio.sleep(attempt)


def make_silence(path, duration):
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(duration), "-c:a", "libmp3lame", "-b:a", "48k", "-y", str(path)], check=True)


def concatenate(parts, destination, directory):
    manifest = directory / "concat.txt"
    manifest.write_text("".join(f"file '{part}'\n" for part in parts))
    rendered = directory / "rendered.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(manifest), "-c", "copy", "-y", str(rendered)], check=True)
    if rendered.stat().st_size < 512:
        raise RuntimeError("Concatenated audio is empty")
    shutil.copy2(rendered, destination)


async def render(text_id, segments, destination, limiter):
    with tempfile.TemporaryDirectory(prefix="pg004-rehema-") as temporary:
        directory = Path(temporary)
        parts = []
        for index, (text, pause) in enumerate(segments):
            speech = directory / f"speech-{index}.mp3"
            if error := await tts(text, speech, limiter):
                return text_id, error
            parts.append(speech)
            if pause:
                silence = directory / f"pause-{index}.mp3"
                make_silence(silence, pause)
                parts.append(silence)
        try:
            concatenate(parts, destination, directory)
        except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
            return text_id, str(error)
    return text_id, None


async def main():
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(".")
    language = root / "content" / "i18n" / "sw-TZ"
    audios = json.loads((language / "audios.json").read_text())
    unknown = set(SEGMENTS).difference(audios)
    if unknown:
        raise SystemExit(f"Unknown audio IDs: {', '.join(sorted(unknown))}")
    limiter = asyncio.Semaphore(3)
    clips = [render(text_id, segments, language / "audio" / audios[text_id], limiter) for text_id, segments in SEGMENTS.items()]
    print(f"Generating {len(clips)} slow, separated Rehema credit clips", flush=True)
    failures = [result for result in await asyncio.gather(*clips) if result[1]]
    if failures:
        raise SystemExit("; ".join(f"{text_id}: {error}" for text_id, error in failures))


if __name__ == "__main__":
    asyncio.run(main())
