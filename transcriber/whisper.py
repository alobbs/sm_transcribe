"""Speech-to-text transcription using faster-whisper."""

import logging
from pathlib import Path

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# Cache the model instance to avoid reloading for each file
_model_cache: dict[str, WhisperModel] = {}


def get_model(model_name: str = "base") -> WhisperModel:
    """
    Get or create a Whisper model instance.

    Args:
        model_name: Whisper model to use (tiny, base, small, medium, large-v3).

    Returns:
        WhisperModel instance.
    """
    if model_name not in _model_cache:
        logger.info(f"Loading Whisper model: {model_name}")
        logger.info("(First run downloads the model from Hugging Face, this may take a moment)")
        _model_cache[model_name] = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
        )
    return _model_cache[model_name]


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS for display."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcribe_audio(
    audio_path: Path,
    output_path: Path | None = None,
    model_name: str = "base",
    include_timestamps: bool = False,
    paragraph_threshold: float = 1.5,
) -> Path | None:
    """
    Transcribe an audio file using faster-whisper.

    Generates both a .txt file and a .srt subtitle file.

    Args:
        audio_path: Path to the input audio file.
        output_path: Path for the output transcript (.txt). If None, uses audio path with .txt extension.
            The .srt file will be saved alongside with the same base name.
        model_name: Whisper model to use.
        include_timestamps: If True, prefix each segment with its timestamp in the .txt file.
        paragraph_threshold: Pause duration (seconds) that triggers a paragraph break in .txt output.

    Returns:
        Path to the transcript .txt file, or None if transcription failed.
    """
    if output_path is None:
        output_path = audio_path.with_suffix(".txt")

    srt_path = output_path.with_suffix(".srt")

    try:
        model = get_model(model_name)

        logger.info(f"Transcribing: {audio_path.name}")
        segments, info = model.transcribe(
            str(audio_path),
            beam_size=5,
            language=None,  # Auto-detect language
            vad_filter=True,  # Filter out non-speech segments
            vad_parameters={
                "min_silence_duration_ms": 500,  # Minimum silence to split segments
            },
        )

        # Collect all segments with timing data
        segment_data: list[tuple[float, float, str]] = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                segment_data.append((segment.start, segment.end, text))

        # Generate TXT content
        txt_lines: list[str] = []
        prev_end: float = 0.0

        for start, end, text in segment_data:
            # Detect paragraph break (long pause since last segment)
            pause_duration = start - prev_end
            if prev_end > 0 and pause_duration > paragraph_threshold:
                txt_lines.append("")  # Blank line for paragraph break

            # Format the line
            if include_timestamps:
                timestamp = format_timestamp(start)
                txt_lines.append(f"[{timestamp}] {text}")
            else:
                txt_lines.append(text)

            prev_end = end

        # Generate SRT content
        srt_lines: list[str] = []
        for i, (start, end, text) in enumerate(segment_data, 1):
            srt_lines.append(str(i))
            srt_lines.append(f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}")
            srt_lines.append(text)
            srt_lines.append("")  # Blank line between entries

        # Write TXT file
        output_path.write_text("\n".join(txt_lines), encoding="utf-8")
        logger.info(f"Transcript saved: {output_path.name}")

        # Write SRT file
        srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
        logger.info(f"Subtitles saved: {srt_path.name}")

        logger.info(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")

        return output_path

    except Exception as e:
        logger.error(f"Failed to transcribe {audio_path}: {e}")
        return None
