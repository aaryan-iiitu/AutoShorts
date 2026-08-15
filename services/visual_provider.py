import os
from typing import List
from urllib.parse import quote_plus
from config.settings import settings
from core.cost_guard import cost_guard
from core.logger import logger
from core.exceptions import AssetFetchError, QuotaExceededError
from models.domain import Script
from services.interfaces import IVisualProvider
from utils.network import get_session
from utils.retry import api_retry

class PexelsUnsplashProvider(IVisualProvider):
    def __init__(self):
        self.session = get_session()
        self.cache = {}  # In-memory cache for search responses during this run

    @api_retry()
    def fetch_assets(self, script: Script, max_assets: int, output_dir: str) -> List[str]:
        logger.info("Fetching visual assets", max_assets=max_assets)
        downloaded_paths = []
        
        # Determine search query from topic
        query = script.topic
        
        # 1. Try Pexels (Videos)
        if settings.pexels_api_key:
            pexels_urls = self._search_pexels(query, max_assets)
            for url in pexels_urls:
                if len(downloaded_paths) >= max_assets:
                    break
                path = self._download_asset(url, output_dir, prefix="pexels_", ext=".mp4")
                if path:
                    downloaded_paths.append(path)
                    
        # 2. Try Unsplash (Images) if we still need assets
        if len(downloaded_paths) < max_assets and settings.unsplash_api_key:
            needed = max_assets - len(downloaded_paths)
            unsplash_urls = self._search_unsplash(query, needed)
            for url in unsplash_urls:
                if len(downloaded_paths) >= max_assets:
                    break
                path = self._download_asset(url, output_dir, prefix="unsplash_", ext=".jpg")
                if path:
                    downloaded_paths.append(path)
                    
        # 3. Local Fallback if no assets could be fetched
        if not downloaded_paths:
            logger.warning("No external assets found. Using local fallback.")
            fallback = self._get_local_fallback(output_dir)
            if fallback:
                downloaded_paths.append(fallback)
        
        if not downloaded_paths:
            raise AssetFetchError("Failed to fetch any visual assets and no local fallback available.")
            
        return downloaded_paths

    def _search_pexels(self, query: str, limit: int) -> List[str]:
        cache_key = f"pexels_{query}"
        if cache_key in self.cache:
            return self.cache[cache_key][:limit]
            
        cost_guard.increment_visual_searches()
        url = f"https://api.pexels.com/videos/search?query={quote_plus(query)}&per_page=15&orientation=portrait"
        headers = {"Authorization": settings.pexels_api_key}
        
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 429:
                raise QuotaExceededError("Pexels rate limit exceeded")
            response.raise_for_status()
            
            data = response.json()
            videos = data.get("videos", [])
            urls = []
            for v in videos:
                files = v.get("video_files", [])
                hd_files = [f for f in files if f.get("quality") == "hd"]
                if hd_files:
                    urls.append(hd_files[0]["link"])
                elif files:
                    urls.append(files[0]["link"])
                    
            self.cache[cache_key] = urls
            return urls[:limit]
        except Exception as e:
            logger.error("Pexels search failed", error=str(e))
            return []

    def _search_unsplash(self, query: str, limit: int) -> List[str]:
        cache_key = f"unsplash_{query}"
        if cache_key in self.cache:
            return self.cache[cache_key][:limit]
            
        cost_guard.increment_visual_searches()
        url = f"https://api.unsplash.com/search/photos?query={quote_plus(query)}&per_page=15&orientation=portrait"
        headers = {"Authorization": f"Client-ID {settings.unsplash_api_key}"}
        
        try:
            response = self.session.get(url, headers=headers)
            if response.status_code == 429:
                raise QuotaExceededError("Unsplash rate limit exceeded")
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            urls = []
            for r in results:
                urls.append(r["urls"]["regular"])
                    
            self.cache[cache_key] = urls
            return urls[:limit]
        except Exception as e:
            logger.error("Unsplash search failed", error=str(e))
            return []

    def _download_asset(self, url: str, output_dir: str, prefix: str = "asset_", ext: str = ".mp4") -> str:
        cost_guard.increment_visual_downloads()
        filename = f"{prefix}{cost_guard.visual_downloads}{ext}"
        filepath = os.path.join(output_dir, filename)
        
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath
        except Exception as e:
            logger.error("Failed to download asset", url=url, error=str(e))
            if os.path.exists(filepath):
                os.remove(filepath)
            return ""

    def _get_local_fallback(self, output_dir: str) -> str:
        fallback_source = os.path.join("assets", "video", "fallback.mp4")
        if os.path.exists(fallback_source):
            dest = os.path.join(output_dir, "fallback.mp4")
            import shutil
            shutil.copy2(fallback_source, dest)
            return dest
        return ""
