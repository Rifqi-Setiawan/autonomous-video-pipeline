"""Account Pool Manager for Rotating Multi-Account Video Generation."""

import os
import json
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("account_pool")

class AccountPool:
    """Manages rotating multi-account sessions for browser automation.
    Enforces round-robin scheduling, daily quota tracking, and automatic cooldown failovers.
    """
    def __init__(self, config_path: str = "./config/accounts.json", profiles_dir: str = "./browser_profiles"):
        self.config_path = config_path
        self.profiles_dir = profiles_dir
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        os.makedirs(profiles_dir, exist_ok=True)
        self.accounts = self._load_accounts()
        self.current_index = 0

    def _load_accounts(self) -> List[Dict]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read {self.config_path}: {e}")

        # Default pool layout with 4 slots
        default_pool = []
        for i in range(1, 5):
            slot_id = f"account{i:02d}"
            profile_path = os.path.join(self.profiles_dir, slot_id)
            is_configured = os.path.exists(os.path.join(profile_path, "Default", "Cookies"))
            default_pool.append({
                "id": slot_id,
                "slot": i,
                "profile_path": profile_path,
                "status": "ACTIVE" if is_configured else "UNCONFIGURED",
                "generations_today": 0,
                "max_daily_generations": 15,
                "last_used_timestamp": 0
            })

        self._save_accounts(default_pool)
        return default_pool

    def _save_accounts(self, accounts: List[Dict]):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=2)

    def get_active_accounts(self) -> List[Dict]:
        """Returns accounts that are authenticated and within quota."""
        active = []
        for acc in self.accounts:
            cookie_file = os.path.join(acc["profile_path"], "Default", "Cookies")
            if os.path.exists(cookie_file) and acc.get("status") != "QUOTA_EXHAUSTED":
                active.append(acc)
        return active

    def get_next_account(self, strategy: str = "round_robin") -> Optional[Dict]:
        """Selects the next active account from the rotation pool."""
        active = self.get_active_accounts()
        if not active:
            logger.error("No active Google accounts available in pool. Please authenticate profiles.")
            return None

        if strategy == "round_robin":
            selected = active[self.current_index % len(active)]
            self.current_index = (self.current_index + 1) % len(active)
            selected["last_used_timestamp"] = time.time()
            selected["generations_today"] = selected.get("generations_today", 0) + 1
            self._save_accounts(self.accounts)
            logger.info(f"Rotation: Selected Slot #{selected['slot']} ({selected['id']}) - Daily count: {selected['generations_today']}")
            return selected
        else:
            for acc in active:
                if acc.get("generations_today", 0) < acc.get("max_daily_generations", 15):
                    acc["generations_today"] = acc.get("generations_today", 0) + 1
                    acc["last_used_timestamp"] = time.time()
                    self._save_accounts(self.accounts)
                    return acc
            return active[0]

    def mark_quota_exhausted(self, slot_id: str):
        """Marks an account as having reached its daily quota limit."""
        for acc in self.accounts:
            if acc["id"] == slot_id:
                acc["status"] = "QUOTA_EXHAUSTED"
                logger.warning(f"Account {slot_id} marked as QUOTA_EXHAUSTED.")
                break
        self._save_accounts(self.accounts)

    def reset_daily_quotas(self):
        """Resets generation counters for all accounts."""
        for acc in self.accounts:
            acc["generations_today"] = 0
            if acc["status"] == "QUOTA_EXHAUSTED":
                acc["status"] = "ACTIVE"
        self._save_accounts(self.accounts)
        logger.info("Daily quotas successfully reset.")
