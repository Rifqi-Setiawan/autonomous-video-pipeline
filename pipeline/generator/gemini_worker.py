"""Playwright Worker for Browser-based AI Video Generation.
Automates 9:16 portrait video generation workflows.
"""

import os
import re
import time
import json
import logging
import urllib.request
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

logger = logging.getLogger("gemini_worker")

REJECTION_KEYWORDS = [
    "tidak bisa membuat video",
    "tidak dapat membuat video",
    "kebijakan video kami",
    "panduan kebijakan",
    "i cannot generate video",
    "i can't generate video",
    "safety policy",
    "violates our policies"
]

QUOTA_KEYWORDS = [
    "limit resets",
    "limit reached",
    "batas pembuatan video",
    "batas anda direset",
    "usage limit"
]

def is_rejected_by_policy(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in REJECTION_KEYWORDS)

def is_quota_exhausted(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in QUOTA_KEYWORDS)

class GeminiVideoWorker:
    """Automates web session to generate portrait video clips."""
    def __init__(self, profile_dir: str):
        self.profile_dir = profile_dir
        os.makedirs(self.profile_dir, exist_ok=True)

    def generate_video(
        self,
        prompt: str,
        dest_path: str,
        aspect_ratio: str = "portrait",
        max_wait_seconds: int = 320,
        page_timeout: int = 45000
    ) -> Dict[str, Any]:
        """Submits video generation prompt and downloads rendered MP4."""
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        logger.info(f"Navigating to video generator with aspect_ratio={aspect_ratio}...")

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=True,
                channel="chrome",
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--window-size=1280,900"
                ],
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            )

            try:
                page = context.new_page()
                page.set_default_timeout(page_timeout)

                page.goto("https://gemini.google.com/videos", wait_until="domcontentloaded")
                time.sleep(3)

                # Dismiss introduction dialogs if present
                for selector in ["button:has-text('Try it')", "button:has-text('Coba')", "button:has-text('Dismiss')", "button:has-text('Mengerti')"]:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=1500):
                            btn.click()
                            time.sleep(1)
                    except Exception:
                        pass

                # Locate prompt input textarea
                input_locator = page.locator("div[contenteditable='true'], textarea, rich-textarea p").first
                input_locator.wait_for(state="visible", timeout=12000)
                input_locator.fill(prompt)
                time.sleep(1)

                # Submit generation request
                submit_btn = page.locator("button[aria-label*='Send'], button[aria-label*='Kirim'], button:has-text('Generate')").first
                submit_btn.click()
                logger.info("Prompt submitted. Polling generation status...")

                # Monitor generation progress
                start_time = time.time()
                while time.time() - start_time < max_wait_seconds:
                    page_text = page.inner_text("body")
                    if is_rejected_by_policy(page_text):
                        logger.warning("Generation blocked by content safety policy filter.")
                        return {"status": "POLICY_REJECTED", "prompt": prompt}

                    if is_quota_exhausted(page_text):
                        logger.warning("Daily generation quota exhausted on this account.")
                        return {"status": "QUOTA_EXHAUSTED", "prompt": prompt}

                    # Check for completed video element
                    video_elem = page.locator("video[src]").first
                    if video_elem.is_visible(timeout=1000):
                        video_url = video_elem.get_attribute("src")
                        if video_url and video_url.startswith("http"):
                            logger.info(f"Video ready. Downloading from: {video_url[:60]}...")
                            urllib.request.urlretrieve(video_url, dest_path)
                            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
                                logger.info(f"Successfully saved video clip: {dest_path}")
                                return {"status": "SUCCESS", "path": dest_path}

                    time.sleep(5)

                logger.error(f"Generation timed out after {max_wait_seconds}s.")
                return {"status": "TIMEOUT", "prompt": prompt}

            except Exception as e:
                logger.error(f"Worker runtime exception: {e}")
                return {"status": "ERROR", "error": str(e)}
            finally:
                context.close()
