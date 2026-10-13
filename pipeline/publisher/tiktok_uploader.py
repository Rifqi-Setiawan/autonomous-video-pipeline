"""TikTok Video Auto-Uploader via Session Automation."""

import os
import time
import json
import logging
from typing import Dict, Any
from playwright.sync_api import sync_playwright

logger = logging.getLogger("tiktok_uploader")

class TikTokUploader:
    """Automates publishing vertical videos to TikTok creator portal."""
    def __init__(self, session_dir: str = "./browser_profiles/tiktok"):
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)

    def upload_video(self, video_path: str, caption: str) -> Dict[str, Any]:
        """Navigates to TikTok upload studio and posts video with caption."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Uploading video to TikTok ({os.path.basename(video_path)})...")
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            try:
                page = context.new_page()
                page.goto("https://www.tiktok.com/creator-center/upload?from=upload", wait_until="networkidle")

                # Locate file input
                file_input = page.locator("input[type='file']").first
                file_input.set_input_files(video_path)
                logger.info("Video file attached. Waiting for processing...")
                time.sleep(8)

                # Set caption
                caption_input = page.locator("div[contenteditable='true'], .public-DraftEditor-content").first
                if caption_input.is_visible(timeout=5000):
                    caption_input.fill(caption)

                # Click post button
                post_btn = page.locator("button:has-text('Post'), button:has-text('Unggah')").first
                post_btn.click()
                time.sleep(10)

                logger.info("Video posted to TikTok.")
                return {"status": "SUCCESS", "platform": "tiktok"}
            except Exception as e:
                logger.error(f"TikTok upload failed: {e}")
                return {"status": "FAILED", "error": str(e)}
            finally:
                context.close()
