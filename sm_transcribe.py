#!/usr/bin/env python3
"""CLI tool for downloading and transcribing TikTok/Instagram videos."""

import logging
import sys
from pathlib import Path

import click

from transcriber.downloader import download_video
from transcriber.audio import extract_audio, cleanup_audio
from transcriber.whisper import transcribe_audio

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def process_url(
    url: str,
    output_dir: Path,
    model: str,
    keep_video: bool,
    timestamps: bool,
    pause_threshold: float,
) -> bool:
    """
    Process a single URL: download, extract audio, transcribe.

    Returns:
        True if successful, False otherwise.
    """
    # Step 1: Download video
    video_path = download_video(url, output_dir)
    if not video_path:
        return False

    # Step 2: Extract audio
    audio_path = extract_audio(video_path)
    if not audio_path:
        return False

    # Step 3: Transcribe
    transcript_path = transcribe_audio(
        audio_path,
        model_name=model,
        include_timestamps=timestamps,
        paragraph_threshold=pause_threshold,
    )
    if not transcript_path:
        cleanup_audio(audio_path)
        return False

    # Cleanup: remove intermediate audio file
    cleanup_audio(audio_path)

    # Optionally remove video file, keep only transcript
    if not keep_video and video_path.exists():
        video_path.unlink()
        logger.info(f"Removed video file (--no-keep-video): {video_path.name}")

    return True


@click.command()
@click.argument("urls", nargs=-1)
@click.option(
    "--file", "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Text file with one URL per line.",
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=".",
    help="Output directory for videos and transcripts. Default: current directory.",
)
@click.option(
    "--model", "-m",
    type=click.Choice(["tiny", "base", "small", "medium", "large-v3"]),
    default="base",
    help="Whisper model to use. Larger models are more accurate but slower.",
)
@click.option(
    "--keep-video/--no-keep-video",
    default=True,
    help="Keep the downloaded video file. Default: keep.",
)
@click.option(
    "--timestamps", "-t",
    is_flag=True,
    help="Include timestamps [MM:SS] at the start of each line.",
)
@click.option(
    "--pause-threshold", "-p",
    type=float,
    default=1.5,
    help="Seconds of pause that triggers a paragraph break. Default: 1.5",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging.",
)
def main(
    urls: tuple[str, ...],
    file: Path | None,
    output: Path,
    model: str,
    keep_video: bool,
    timestamps: bool,
    pause_threshold: float,
    verbose: bool,
) -> None:
    """
    Download and transcribe TikTok/Instagram videos.

    Pass URLs as arguments or use --file to read from a text file.

    Examples:

        sm_transcribe https://www.tiktok.com/@user/video/123

        sm_transcribe --file urls.txt --model small

        sm_transcribe -o transcripts --no-keep-video URL1 URL2

        sm_transcribe --timestamps --pause-threshold 2.0 URL
    """
    # Set log level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Collect URLs from arguments and file
    all_urls: list[str] = list(urls)

    if file:
        file_urls = [
            line.strip()
            for line in file.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        all_urls.extend(file_urls)

    if not all_urls:
        click.echo("Error: No URLs provided. Pass URLs as arguments or use --file.", err=True)
        click.echo("Run 'sm_transcribe --help' for usage information.", err=True)
        sys.exit(1)

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output.absolute()}")
    logger.info(f"Using Whisper model: {model}")
    logger.info(f"Processing {len(all_urls)} URL(s)")

    # Process each URL
    success_count = 0
    fail_count = 0

    for i, url in enumerate(all_urls, 1):
        logger.info(f"[{i}/{len(all_urls)}] Processing: {url}")

        if process_url(url, output, model, keep_video, timestamps, pause_threshold):
            success_count += 1
        else:
            fail_count += 1
            logger.warning(f"Failed to process: {url}")

    # Summary
    logger.info("-" * 40)
    logger.info(f"Completed: {success_count} successful, {fail_count} failed")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
