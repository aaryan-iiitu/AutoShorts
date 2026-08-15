import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config.settings import settings
from core.exceptions import UploadError
from core.logger import logger
from services.interfaces import IYouTubeUploader
from utils.retry import api_retry

class YouTubeUploader(IYouTubeUploader):
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        
    def _get_credentials(self) -> Credentials:
        if not os.path.exists(settings.youtube_credentials_file):
            raise UploadError(f"Missing YouTube credentials at {settings.youtube_credentials_file}. Run scripts/youtube_auth.py first.")
            
        with open(settings.youtube_credentials_file, "r") as f:
            creds_data = json.load(f)
            
        return Credentials(
            token=creds_data.get("token"),
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=self.scopes
        )

    @api_retry()
    def upload_video(self, video_path: str, title: str, description: str, privacy_status: str = "private") -> str:
        logger.info("Starting YouTube upload", title=title, privacy=privacy_status)
        
        try:
            creds = self._get_credentials()
            youtube = build("youtube", "v3", credentials=creds)
            
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["shorts", "autoshorts", "ai"],
                    "categoryId": "22"  # People & Blogs
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                }
            }
            
            media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
            
            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            response = request.execute()
            video_id = response.get("id")
            
            if not video_id:
                raise UploadError("YouTube API did not return a video ID.")
                
            url = f"https://www.youtube.com/shorts/{video_id}"
            logger.info("Upload successful", url=url)
            return url
            
        except Exception as e:
            logger.error("YouTube upload failed", error=str(e))
            raise UploadError(f"YouTube Upload Failed: {str(e)}")
