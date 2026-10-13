"""Multi-Platform Publishing Orchestrator with Automated Storage Lifecycle Archival."""

import os
import glob
import json
import shutil
import logging
from typing import Dict, Any, Optional
from .youtube_uploader import YouTubeUploader
from .tiktok_uploader import TikTokUploader

logger = logging.getLogger("publisher")

class MultiPlatformPublisher:
    """Manages publishing across YouTube and TikTok, and handles post-publish archival."""
    def __init__(
        self,
        youtube_token_path: str = "./config/youtube_token.json",
        tiktok_session_dir: str = "./browser_profiles/tiktok",
        archive_dir: str = "./archive"
    ):
        self.youtube = YouTubeUploader(token_path=youtube_token_path)
        self.tiktok = TikTokUploader(session_dir=tiktok_session_dir)
        self.archive_dir = archive_dir

    def publish(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[list] = None,
        target: str = "all"
    ) -> Dict[str, Any]:
        results = {}

        if target in ("all", "youtube"):
            try:
                yt_res = self.youtube.upload_short(video_path, title, description, tags)
                results["youtube"] = yt_res
            except Exception as e:
                logger.error(f"YouTube publishing failed: {e}")
                results["youtube"] = {"status": "FAILED", "error": str(e)}

        if target in ("all", "tiktok"):
            try:
                tt_caption = f"{title}\n\n{description[:100]}"
                tt_res = self.tiktok.upload_video(video_path, tt_caption)
                results["tiktok"] = tt_res
            except Exception as e:
                logger.error(f"TikTok publishing failed: {e}")
                results["tiktok"] = {"status": "FAILED", "error": str(e)}

        # Storage Lifecycle: If publication succeeded, archive large media to cold storage
        if any(r.get("status") == "SUCCESS" for r in results.values()):
            self.archive_media(video_path)

        return results

    def archive_media(self, video_path: str) -> Optional[str]:
        """Moves uploaded video to archive directory, creating a lightweight symlink."""
        if not os.path.exists(video_path) or os.path.islink(video_path):
            return None

        os.makedirs(self.archive_dir, exist_ok=True)
        base = os.path.basename(video_path)
        dest = os.path.join(self.archive_dir, base)

        try:
            if os.path.exists(dest):
                os.remove(dest)
            shutil.move(video_path, dest)
            os.symlink(os.path.abspath(dest), video_path)
            logger.info(f"Storage Lifecycle: Moved {base} to cold archive {dest} (symlinked in place).")
            return dest
        except Exception as e:
            logger.warning(f"Failed to archive {base}: {e}")
            return None
