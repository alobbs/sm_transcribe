"""Video downloader using yt-dlp."""

import logging
import re
from pathlib import Path

import yt_dlp

logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> str:
    """Extract video ID from TikTok or Instagram URL."""
    # TikTok: https://www.tiktok.com/@user/video/1234567890
    tiktok_match = re.search(r"/video/(\d+)", url)
    if tiktok_match:
        return tiktok_match.group(1)

    # Instagram: https://www.instagram.com/reel/ABC123/ or /p/ABC123/
    instagram_match = re.search(r"/(reel|p)/([A-Za-z0-9_-]+)", url)
    if instagram_match:
        return instagram_match.group(2)

    # Fallback: use hash of URL
    return str(abs(hash(url)))[:12]


def download_video(url: str, output_dir: Path) -> Path | None:
    """
    Download a video from TikTok or Instagram.

    Args:
        url: The video URL to download.
        output_dir: Directory to save the video.

    Returns:
        Path to the downloaded video, or None if download failed.
    """
    video_id = extract_video_id(url)
    output_template = str(output_dir / f"{video_id}.%(ext)s")

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading: {url}")
            info = ydl.extract_info(url, download=True)

            # Get the actual output filename
            if info:
                ext = info.get("ext", "mp4")
                output_path = output_dir / f"{video_id}.{ext}"
                if output_path.exists():
                    logger.info(f"Downloaded: {output_path.name}")
                    return output_path

            # Fallback: look for any file matching the video_id
            for file in output_dir.glob(f"{video_id}.*"):
                if file.suffix in [".mp4", ".webm", ".mkv"]:
                    logger.info(f"Downloaded: {file.name}")
                    return file

            logger.error(f"Download completed but file not found for: {url}")
            return None

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Failed to download {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return None
