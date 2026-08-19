"""Restore cached pg009 audio filenames with corrected Rehema v2 bytes."""

from __future__ import annotations

import shutil

from fix_pg009_figure3_rehema import LANGUAGE, TARGET_IDS, VERSION


def main() -> None:
    audio_dir = LANGUAGE / "audio"
    aliases = 0
    for text_id in TARGET_IDS:
        source = audio_dir / f"{text_id}_{VERSION}.mp3"
        if not source.is_file():
            raise SystemExit(f"Missing corrected Rehema clip: {source}")
        for legacy_name in (
            f"{text_id}_rehema_image_v1.mp3",
            f"{text_id}_male.mp3",
        ):
            shutil.copyfile(source, audio_dir / legacy_name)
            aliases += 1
    print(f"Created {aliases} cached-name aliases from corrected Rehema clips")


if __name__ == "__main__":
    main()
