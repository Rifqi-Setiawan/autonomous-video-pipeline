"""Batch Scene Generator orchestrating clip production across account pools."""

import os
import time
import logging
from typing import Dict, List, Any
from .account_pool import AccountPool
from .gemini_worker import GeminiVideoWorker

logger = logging.getLogger("batch_generator")

class BatchSceneGenerator:
    """Coordinates multi-scene video generation using rotating account slots."""
    def __init__(self, pool: AccountPool, output_dir: str):
        self.pool = pool
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for scene in scenes:
            scene_id = scene.get("scene_id", len(results) + 1)
            prompt = scene.get("prompt", "")
            dest_file = os.path.join(self.output_dir, f"scene_{scene_id:02d}.mp4")

            if os.path.exists(dest_file) and os.path.getsize(dest_file) > 100000:
                logger.info(f"Scene {scene_id} already exists on disk. Skipping regeneration.")
                results.append({"scene_id": scene_id, "status": "EXISTS", "path": dest_file})
                continue

            max_retries = 3
            success = False
            for attempt in range(max_retries):
                account = self.pool.get_next_account()
                if not account:
                    logger.error("No available accounts to continue generation.")
                    break

                logger.info(f"Generating Scene {scene_id:02d} on account slot {account['id']} (attempt {attempt+1})...")
                worker = GeminiVideoWorker(profile_dir=account["profile_path"])
                res = worker.generate_video(prompt=prompt, dest_path=dest_file)

                if res.get("status") == "SUCCESS":
                    results.append({"scene_id": scene_id, "status": "SUCCESS", "path": dest_file})
                    success = True
                    break
                elif res.get("status") == "QUOTA_EXHAUSTED":
                    self.pool.mark_quota_exhausted(account["id"])
                    logger.warning(f"Rotating away from exhausted account {account['id']}...")
                else:
                    logger.warning(f"Scene {scene_id} attempt {attempt+1} ended with: {res.get('status')}")
                    time.sleep(3)

            if not success:
                results.append({"scene_id": scene_id, "status": "FAILED"})

        return results
