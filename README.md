# sm_transcribe

Download TikTok and Instagram videos and transcribe them locally using Whisper. No cloud APIs, no subscriptions: everything runs on your machine.

## Installation

```bash
pip install sm_transcribe
```

**Requires ffmpeg** installed on your system:
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg`

## Usage

```bash
# Single video
sm_transcribe https://www.tiktok.com/@user/video/123

# Multiple videos
sm_transcribe URL1 URL2 URL3

# From a file (one URL per line)
sm_transcribe --file urls.txt

# Use a larger model for better accuracy
sm_transcribe --model large-v3 URL
```

## Output

For each video, generates:
- `{video_id}.mp4` — Downloaded video
- `{video_id}.txt` — Transcript with paragraph breaks
- `{video_id}.srt` — Subtitles for video players

## Options

| Option | Description |
|--------|-------------|
| `-o, --output DIR` | Output directory (default: current) |
| `-m, --model MODEL` | Whisper model: `tiny`, `base`, `small`, `medium`, `large-v3` |
| `-t, --timestamps` | Add `[MM:SS]` timestamps to transcript |
| `-p, --pause-threshold SEC` | Pause duration for paragraph breaks (default: 1.5) |
| `--no-keep-video` | Delete video after transcription, keep only transcript |
| `-v, --verbose` | Verbose logging |

## Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | ~75MB | Fastest | Lower |
| `base` | ~150MB | Fast | Good |
| `small` | ~500MB | Medium | Better |
| `medium` | ~1.5GB | Slow | High |
| `large-v3` | ~3GB | Slowest | Highest |

Models download automatically on first use.

## License

MIT
