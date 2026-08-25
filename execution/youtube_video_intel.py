#!/usr/bin/env python3
"""
youtube_video_intel.py: fetch metadata and transcript for any YouTube video.

Used by directives/youtube_agent.md. Deterministic tool: give it a URL or video ID,
it writes metadata JSON and a clean plain-text transcript into .tmp/youtube/.

Usage:
    python3 execution/youtube_video_intel.py "https://www.youtube.com/watch?v=VIDEOID"
    python3 execution/youtube_video_intel.py VIDEOID --no-transcript

Notes (learned 2026-08-20):
- YouTube's web caption endpoints return empty bodies (anti-bot). The fix is
  yt-dlp with the android player client: --extractor-args "youtube:player_client=android"
- Auto captions (asr) are fine for study purposes. VTT is deduplicated because
  auto captions repeat each line across overlapping cues.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / ".tmp" / "youtube"


def find_yt_dlp():
    for candidate in [shutil.which("yt-dlp"), str(Path.home() / "Library/Python/3.9/bin/yt-dlp")]:
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit("yt-dlp not found. Install with: python3 -m pip install --user yt-dlp")


def video_id_from(arg):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", arg)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", arg):
        return arg
    sys.exit(f"Could not parse a video ID from: {arg}")


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"Command failed: {' '.join(cmd)}\n{result.stderr[-2000:]}")
    return result.stdout


def clean_vtt(vtt_path):
    """VTT to plain text. Auto captions repeat lines across cues, so dedupe consecutively."""
    out, seen_last = [], None
    for line in vtt_path.read_text(encoding="utf-8").splitlines():
        if "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:")) or not line.strip():
            continue
        text = re.sub(r"<[^>]+>", "", line).strip()
        if text and text != seen_last:
            out.append(text)
            seen_last = text
    return " ".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="YouTube URL or 11-char video ID")
    parser.add_argument("--no-transcript", action="store_true", help="metadata only")
    args = parser.parse_args()

    vid = video_id_from(args.url)
    url = f"https://www.youtube.com/watch?v={vid}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    yt = find_yt_dlp()
    extractor = "youtube:player_client=android"

    meta_raw = json.loads(run([yt, "--skip-download", "--dump-json", "--extractor-args", extractor, url]))
    meta = {
        "id": vid,
        "title": meta_raw.get("title"),
        "channel": meta_raw.get("channel") or meta_raw.get("uploader") or meta_raw.get("uploader_id"),
        "upload_date": meta_raw.get("upload_date"),
        "duration_s": meta_raw.get("duration"),
        "view_count": meta_raw.get("view_count"),
        "like_count": meta_raw.get("like_count"),
        "description": meta_raw.get("description"),
        "tags": meta_raw.get("tags", []),
        "chapters": meta_raw.get("chapters"),
    }
    meta_path = OUT_DIR / f"{vid}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"metadata: {meta_path}")

    if not args.no_transcript:
        stem = OUT_DIR / vid
        run([yt, "--skip-download", "--write-auto-sub", "--write-sub", "--sub-lang", "en",
             "--sub-format", "vtt", "--extractor-args", extractor, "-o", str(stem), url])
        vtts = sorted(OUT_DIR.glob(f"{vid}*.vtt"))
        if not vtts:
            print("warning: no English captions available for this video")
        else:
            text = clean_vtt(vtts[0])
            txt_path = OUT_DIR / f"{vid}.transcript.txt"
            txt_path.write_text(text, encoding="utf-8")
            for v in vtts:
                v.unlink()
            print(f"transcript: {txt_path} ({len(text.split())} words)")

    print(f"\n{meta['title']} | {meta['channel']} | {meta['view_count']} views | {meta['duration_s']}s")


if __name__ == "__main__":
    main()
