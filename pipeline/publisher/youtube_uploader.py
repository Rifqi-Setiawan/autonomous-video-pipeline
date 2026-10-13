"""YouTube Video Auto-Uploader via YouTube Data API v3."""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger("youtube_uploader")

class YouTubeUploader:
    """Manages automated uploading to YouTube Shorts."""
    def __init__(self, token_path: str = "./config/youtube_token.json"):
        self.token_path = token_path

    def _get_service(self):
        if not os.path.exists(self.token_path):
            raise FileNotFoundError(f"OAuth token not found at {self.token_path}. Please authenticate first.")

        with open(self.token_path, "r", encoding="utf-8") as f:
            info = json.load(f)

        creds = Credentials(
            token=info.get("token"),
            refresh_token=info.get("refresh_token"),
            token_uri=info.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=info.get("client_id"),
            client_secret=info.get("client_secret"),
            scopes=info.get("scopes", ["https://www.googleapis.com/auth/youtube.upload"])
        )
        return build("youtube", "v3", credentials=creds)

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        category_id: str = "28",
        privacy_status: str = "public"
    ) -> Dict[str, Any]:
        """Uploads video to YouTube Shorts with metadata and tags."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        youtube = self._get_service()
        tags = tags or ["shorts", "educational", "history", "science"]

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(
            video_path,
            chunksize=4 * 1024 * 1024,
            resumable=True,
            mimetype="video/mp4"
        )

        logger.info(f"Uploading '{title}' to YouTube ({os.path.getsize(video_path)/1024/1024:.2f} MB)...")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        video_url = f"https://www.youtube.com/shorts/{video_id}"
        logger.info(f"Upload successful: {video_url}")
        return {"status": "SUCCESS", "video_id": video_id, "url": video_url}
