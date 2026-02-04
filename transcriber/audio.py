"""Audio extraction using ffmpeg."""

import logging
from pathlib import Path

import ffmpeg

logger = logging.getLogger(__name__)


def extract_audio(video_path: Path, output_path: Path | None = None) -> Path | None:
    """
    Extract audio from a video file and convert to 16kHz WAV for Whisper.

    Args:
        video_path: Path to the input video file.
        output_path: Path for the output audio file. If None, uses video path with .wav extension.

    Returns:
        Path to the extracted audio file, or None if extraction failed.
    """
    if output_path is None:
        output_path = video_path.with_suffix(".wav")

    try:
        logger.info(f"Extracting audio: {video_path.name}")

        # Extract audio and convert to 16kHz mono WAV (optimal for Whisper)
        stream = ffmpeg.input(str(video_path))
        stream = ffmpeg.output(
            stream,
            str(output_path),
            acodec="pcm_s16le",
            ar=16000,
            ac=1,
        )
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        if output_path.exists():
            logger.info(f"Audio extracted: {output_path.name}")
            return output_path

        logger.error(f"Audio extraction completed but file not found: {output_path}")
        return None

    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error extracting audio from {video_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error extracting audio from {video_path}: {e}")
        return None


def cleanup_audio(audio_path: Path) -> None:
    """Remove intermediate audio file after transcription."""
    try:
        if audio_path.exists():
            audio_path.unlink()
            logger.debug(f"Cleaned up: {audio_path.name}")
    except Exception as e:
        logger.warning(f"Failed to clean up {audio_path}: {e}")
