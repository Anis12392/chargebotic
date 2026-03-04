#!/usr/bin/env python3
"""
Transcribe all downloaded MP4 files in .tmp/reels/ using Whisper.
Saves progress incrementally so it can be resumed if interrupted.

Usage:
    python3 execution/transcribe_reels.py
    python3 execution/transcribe_reels.py --whisper-model small
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import whisper


def extract_audio(video_path: Path) -> Path:
    audio_path = video_path.with_suffix(".wav")
    if audio_path.exists():
        return audio_path
    subprocess.run(
        ["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le",
         "-ar", "16000", "-ac", "1", str(audio_path), "-y"],
        capture_output=True, check=True,
    )
    return audio_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--whisper-model", default="base")
    parser.add_argument("--reels-dir", default=".tmp/reels")
    parser.add_argument("--output", default=".tmp/transcripts.md")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    reels_dir = project_root / args.reels_dir
    output_file = project_root / args.output
    progress_file = project_root / ".tmp/transcribe_progress.json"

    # Load previous progress
    progress = {}
    if progress_file.exists():
        progress = json.loads(progress_file.read_text())

    videos = sorted(reels_dir.glob("*.mp4"))
    print(f"Found {len(videos)} videos. Already transcribed: {len(progress)}")

    print(f"Loading Whisper model: {args.whisper_model}")
    model = whisper.load_model(args.whisper_model)

    for i, video in enumerate(videos, 1):
        name = video.stem
        if name in progress:
            continue

        print(f"[{i}/{len(videos)}] {name}")
        try:
            audio = extract_audio(video)
            result = model.transcribe(str(audio), language="fr")
            transcript = result["text"].strip()
            progress[name] = transcript

            # Save progress after each transcription
            progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2))

            if i % 50 == 0:
                print(f"  Progress saved ({len(progress)} done)")
        except Exception as e:
            print(f"  ERROR: {e}")
            progress[name] = f"[Error: {e}]"
            progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2))

    # Compile markdown
    print(f"\nCompiling transcripts to {output_file}")
    lines = [
        "# Transcripts — Instagram Reels @agencepersonnelle",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Total videos:** {len(videos)}",
        f"**Transcribed:** {len([v for v in progress.values() if not v.startswith('[Error')])}",
        "",
        "---",
        "",
    ]

    for video in videos:
        name = video.stem
        transcript = progress.get(name, "_No transcript_")
        lines.extend([f"## {name}", "", transcript, "", "---", ""])

    output_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Done! Transcripts saved to {output_file}")


if __name__ == "__main__":
    main()
