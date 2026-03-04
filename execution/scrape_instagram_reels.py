#!/usr/bin/env python3
"""
Download all reels from a public Instagram profile and transcribe them using Whisper.

Usage:
    python3 execution/scrape_instagram_reels.py --profile agencepersonnelle
    python3 execution/scrape_instagram_reels.py --profile agencepersonnelle --whisper-model small
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import instaloader
import whisper


def download_reels(profile_name: str, output_dir: Path) -> list[dict]:
    """Download all video reels from a public Instagram profile."""
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern="",
    )

    print(f"Loading profile: {profile_name}")
    profile = instaloader.Profile.from_username(L.context, profile_name)

    videos = []
    print("Fetching posts...")
    for post in profile.get_posts():
        if not post.is_video:
            continue

        date_str = post.date_utc.strftime("%Y-%m-%d")
        safe_shortcode = post.shortcode
        filename = f"{date_str}_{safe_shortcode}"
        video_path = output_dir / f"{filename}.mp4"

        if video_path.exists():
            print(f"  Already downloaded: {filename}")
        else:
            print(f"  Downloading: {filename}")
            L.download_post(post, target=output_dir)
            # instaloader saves with its own naming, find and rename
            for f in output_dir.iterdir():
                if f.suffix == ".mp4" and safe_shortcode not in f.name:
                    continue
                if f.suffix == ".mp4" and f.name != video_path.name:
                    f.rename(video_path)
                    break

        # Clean up non-video files instaloader may have created
        for f in output_dir.iterdir():
            if f.suffix not in (".mp4", ".wav", ".md"):
                f.unlink()

        caption = (post.caption or "")[:100].replace("\n", " ")
        videos.append({
            "path": video_path,
            "date": date_str,
            "shortcode": safe_shortcode,
            "caption": caption,
            "url": f"https://www.instagram.com/p/{safe_shortcode}/",
        })

    print(f"Found {len(videos)} videos total.")
    return videos


def extract_audio(video_path: Path) -> Path:
    """Extract audio from video as 16kHz mono WAV (optimal for Whisper)."""
    audio_path = video_path.with_suffix(".wav")
    if audio_path.exists():
        return audio_path

    subprocess.run(
        [
            "ffmpeg", "-i", str(video_path),
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            str(audio_path), "-y",
        ],
        capture_output=True,
        check=True,
    )
    return audio_path


def transcribe_audio(audio_path: Path, model) -> str:
    """Transcribe audio file using Whisper."""
    result = model.transcribe(str(audio_path), language="fr")
    return result["text"].strip()


def compile_transcripts(videos: list[dict], transcripts: dict, output_path: Path):
    """Write all transcripts to a single markdown file."""
    lines = [
        f"# Transcripts — Instagram Reels",
        f"",
        f"**Profile:** agencepersonnelle",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Total videos:** {len(videos)}",
        f"",
        "---",
        "",
    ]

    for v in sorted(videos, key=lambda x: x["date"], reverse=True):
        shortcode = v["shortcode"]
        lines.append(f"## {v['date']} — {v['shortcode']}")
        lines.append(f"")
        lines.append(f"**Link:** {v['url']}")
        if v["caption"]:
            lines.append(f"**Caption:** {v['caption']}")
        lines.append(f"")
        transcript = transcripts.get(shortcode, "_No transcript available_")
        lines.append(transcript)
        lines.append(f"")
        lines.append("---")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nTranscripts written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape Instagram reels and transcribe")
    parser.add_argument("--profile", required=True, help="Instagram username")
    parser.add_argument("--whisper-model", default="base", help="Whisper model size (tiny, base, small, medium, large)")
    parser.add_argument("--output-dir", default=".tmp/reels", help="Directory for downloaded videos")
    parser.add_argument("--output-file", default=".tmp/transcripts.md", help="Output markdown file")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / args.output_dir
    output_file = project_root / args.output_file
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Download reels
    print("=== Step 1: Downloading reels ===")
    videos = download_reels(args.profile, output_dir)

    if not videos:
        print("No videos found. Exiting.")
        return

    # Step 2: Extract audio
    print("\n=== Step 2: Extracting audio ===")
    for v in videos:
        if v["path"].exists():
            print(f"  Extracting audio: {v['path'].name}")
            extract_audio(v["path"])
        else:
            print(f"  Video file not found: {v['path'].name}")

    # Step 3: Transcribe
    print(f"\n=== Step 3: Transcribing with Whisper ({args.whisper_model}) ===")
    model = whisper.load_model(args.whisper_model)
    transcripts = {}
    for i, v in enumerate(videos, 1):
        audio_path = v["path"].with_suffix(".wav")
        if not audio_path.exists():
            print(f"  [{i}/{len(videos)}] Skipping {v['shortcode']} (no audio)")
            continue
        print(f"  [{i}/{len(videos)}] Transcribing {v['shortcode']}...")
        transcripts[v["shortcode"]] = transcribe_audio(audio_path, model)

    # Step 4: Compile
    print("\n=== Step 4: Compiling transcripts ===")
    compile_transcripts(videos, transcripts, output_file)

    print("\nDone!")


if __name__ == "__main__":
    main()
