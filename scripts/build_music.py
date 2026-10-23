#!/usr/bin/env python3
"""Build the web music library from the local FLAC collection.

Why this exists
---------------
The browser player must stream from the *same origin* as the site. The old
player pointed at ``http://127.0.0.1:8765`` which only worked on the machine
that ran a file server, and is blocked as mixed content on an HTTPS page.

This script:
  1. encodes a curated list of FLAC files to 320 kbps MP3 (lossless source,
     transparent for web playback, ~10x smaller than FLAC),
  2. writes ``web/public/music/NN.mp3``,
  3. writes ``web/public/music/manifest.json`` which the player reads.

Re-running is safe: existing outputs are overwritten and the manifest is
regenerated from the TRACKS list.

Usage:
    python scripts/build_music.py            # build + report
    python scripts/build_music.py --dry-run  # only check sources exist
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(os.environ.get("NEMT_FLAC_DIR", r"E:\FLAC"))
OUT_DIR = REPO_ROOT / "web" / "public" / "music"
BITRATE = os.environ.get("NEMT_MUSIC_BITRATE", "320k")

# (source file inside SOURCE_DIR, title, artist)
TRACKS: list[tuple[str, str, str]] = [
    ("1个球-大雨还在下.flac", "大雨还在下", "1个球"),
    ("3611 - 陈子晴.flac", "3611", "陈子晴"),
    ("9420 - 麦小兜.flac", "9420", "麦小兜"),
    ("阿梨粤-秒针.flac", "秒针", "阿梨粤"),
    ("阿木-追梦人.flac", "追梦人", "阿木"),
    ("阿冗-你的答案1.flac", "你的答案", "阿冗"),  # the plain copy has 4 corrupt FLAC frames
    ("阿肆-热爱105°C的你.flac", "热爱105°C的你", "阿肆"),
    ("安苏羽&傅梦彤-潮汐(Natural).flac", "潮汐 (Natural)", "安苏羽 / 傅梦彤"),
    # 周杰伦-晴天.flac (and its duplicate) both fail to decode; 青花瓷 is clean.
    ("周杰伦-青花瓷.flac", "青花瓷", "周杰伦"),
    ("周杰伦-稻香.flac", "稻香", "周杰伦"),
    ("周杰伦-夜曲.flac", "夜曲", "周杰伦"),
    ("陈奕迅-十年.flac", "十年", "陈奕迅"),
    ("陈奕迅-孤勇者.flac", "孤勇者", "陈奕迅"),
    ("Beyond-光辉岁月.flac", "光辉岁月", "Beyond"),
    ("陈慧娴-千千阙歌.flac", "千千阙歌", "陈慧娴"),
    ("G.E.M.邓紫棋-光年之外.flac", "光年之外", "G.E.M.邓紫棋"),
    ("林俊杰-江南.flac", "江南", "林俊杰"),
    ("Eagles-Hotel California.flac", "Hotel California", "Eagles"),
    ("Carpenters-Yesterday Once More.flac", "Yesterday Once More", "Carpenters"),
    ("Westlife-My Love.flac", "My Love", "Westlife"),
]


def find_tool(name: str) -> str:
    override = os.environ.get(name.upper())
    if override and Path(override).is_file():
        return override
    found = shutil.which(name)
    if found:
        return found
    winget = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
    if winget.is_file():
        return str(winget)
    raise SystemExit(f"{name} not found; set {name.upper()}=<path>")


def probe_duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return round(float(result.stdout.strip()), 1)
    except ValueError:
        return 0.0


def encode(ffmpeg: str, source: Path, target: Path, title: str, artist: str) -> None:
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map_metadata",
            "-1",  # drop embedded cover art: it would bloat every request
            "-codec:a",
            "libmp3lame",
            "-b:a",
            BITRATE,
            "-id3v2_version",
            "3",
            "-metadata",
            f"title={title}",
            "-metadata",
            f"artist={artist}",
            str(target),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    missing = [item[0] for item in TRACKS if not (SOURCE_DIR / item[0]).is_file()]
    if missing:
        print("MISSING SOURCE FILES:")
        for name in missing:
            print("  -", name)
        return 1
    print(f"sources ok: {len(TRACKS)} tracks in {SOURCE_DIR}")

    if args.dry_run:
        total = sum((SOURCE_DIR / item[0]).stat().st_size for item in TRACKS)
        print(f"dry run: {total / 1024 / 1024:.1f} MB of FLAC would be encoded at {BITRATE}")
        return 0

    ffmpeg = find_tool("ffmpeg")
    ffprobe = find_tool("ffprobe")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []
    started = time.time()
    total_out = 0
    for index, (filename, title, artist) in enumerate(TRACKS, start=1):
        source = SOURCE_DIR / filename
        track_id = f"{index:02d}"
        target = OUT_DIR / f"{track_id}.mp3"
        t0 = time.time()
        encode(ffmpeg, source, target, title, artist)
        size = target.stat().st_size
        total_out += size
        duration = probe_duration(ffprobe, target)
        manifest.append(
            {
                "id": track_id,
                "title": title,
                "artist": artist,
                "file": f"{track_id}.mp3",
                "bytes": size,
                "durationSec": duration,
                "source": filename,
            }
        )
        print(
            f"[{index:02d}/{len(TRACKS)}] {title:<18} {size / 1024 / 1024:5.1f} MB "
            f"{duration:6.1f}s  ({time.time() - t0:.1f}s)"
        )

    payload = {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bitrate": BITRATE,
        "count": len(manifest),
        "tracks": manifest,
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"\ndone: {len(manifest)} tracks, {total_out / 1024 / 1024:.1f} MB, "
        f"{time.time() - started:.1f}s -> {OUT_DIR}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
