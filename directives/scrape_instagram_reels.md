# Scrape Instagram Reels & Transcribe

## Goal
Download all video reels from a public Instagram profile and transcribe the audio into text.

## Inputs
- Instagram profile username (must be public)
- Whisper model size (default: `base`)

## Tools / Scripts
1. **`execution/scrape_instagram_reels.py`** — Downloads all reels from a profile
   - Uses `instaloader` to fetch video posts
   - Saves MP4 files to `.tmp/reels/`
   - Usage: `python3 execution/scrape_instagram_reels.py --profile <username>`

2. **`execution/transcribe_reels.py`** — Transcribes all downloaded MP4 files
   - Extracts audio with `ffmpeg` (16kHz mono WAV)
   - Transcribes with local Whisper (`base` model by default)
   - Saves progress incrementally to `.tmp/transcribe_progress.json` (resumable)
   - Compiles all transcripts into `.tmp/transcripts.md`
   - Usage: `python3 execution/transcribe_reels.py [--whisper-model small]`

## Outputs
- `.tmp/reels/*.mp4` — Downloaded video files
- `.tmp/reels/*.wav` — Extracted audio (intermediate)
- `.tmp/transcribe_progress.json` — Incremental progress (resumable)
- `.tmp/transcripts.md` — Final compiled transcripts

## Dependencies
- `instaloader` — Instagram scraping
- `openai-whisper` — Local speech-to-text
- `ffmpeg` — Audio extraction (system dependency)

## Edge Cases & Learnings
- **Instagram rate limiting**: instaloader handles 403 retries automatically, but scraping 1000+ posts is slow (~10-20 min for downloads alone)
- **Large accounts**: The `agencepersonnelle` account had 975+ reels (5.6 GB). Consider limiting with script modifications if you only need recent content.
- **Duplicate timestamps**: Multiple posts at the same second can cause filename collisions in instaloader's default naming. The scrape script uses shortcodes to avoid this.
- **Transcription time**: ~975 videos with Whisper `base` model on CPU takes several hours. Use `small` for better accuracy (slower) or `tiny` for speed.
- **Language**: Default transcription language is `fr` (French). Change in the script if needed.
- **Resumability**: The transcribe script saves after each file, so you can stop and restart without losing progress.

## Workflow
1. Run the download script (can be stopped when enough videos are collected)
2. Run the transcription script (resumable)
3. Review `.tmp/transcripts.md`
