"""Version one page's audio filenames, update mappings, and remove old files."""

import argparse
import json
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--page", required=True)
    parser.add_argument("--suffix", required=True)
    args = parser.parse_args()

    root = Path(args.root)
    language = root / "content" / "i18n" / "sw-TZ"
    audio_path = language / "audios.json"
    audios = json.loads(audio_path.read_text())
    audio_dir = language / "audio"
    changes = []
    for text_id, old_name in list(audios.items()):
        if not text_id.startswith(f"{args.page}_"):
            continue
        old_path = audio_dir / old_name
        if not old_path.is_file():
            raise SystemExit(f"Missing source audio: {old_path}")
        new_name = f"{text_id}_{args.suffix}.mp3"
        new_path = audio_dir / new_name
        shutil.copy2(old_path, new_path)
        audios[text_id] = new_name
        changes.append((text_id, old_name, new_name, old_path))

    audio_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n")
    preloader_path = root / "assets" / "offline-preloader.js"
    preloader = preloader_path.read_text()
    for text_id, old_name, new_name, _ in changes:
        old_entry = f'"{text_id}":"{old_name}"'
        new_entry = f'"{text_id}":"{new_name}"'
        if old_entry not in preloader:
            raise SystemExit(f"Missing offline mapping: {old_entry}")
        preloader = preloader.replace(old_entry, new_entry, 1)
    preloader_path.write_text(preloader)
    for _, _, _, old_path in changes:
        old_path.unlink()
    print(f"Versioned {len(changes)} clips for {args.page}", flush=True)


if __name__ == "__main__":
    main()
