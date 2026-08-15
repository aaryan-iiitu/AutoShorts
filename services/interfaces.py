from abc import ABC, abstractmethod
from typing import List
from models.domain import Script, VideoState

class ITopicGenerator(ABC):
    @abstractmethod
    def generate_topic(self, recent_topics: List[str]) -> str:
        """Generate a novel topic that hasn't been used recently."""
        pass

class IScriptGenerator(ABC):
    @abstractmethod
    def generate_script(self, topic: str) -> Script:
        """Generate a script containing multiple narration segments for the topic."""
        pass

class ITTSService(ABC):
    @abstractmethod
    def generate_audio(self, text: str, output_path: str) -> float:
        """Generate text-to-speech audio and save to output_path. Returns duration in seconds."""
        pass

class IVisualProvider(ABC):
    @abstractmethod
    def fetch_assets(self, script: Script, max_assets: int, output_dir: str) -> List[str]:
        """Fetch free stock video/image assets relevant to the script. Must obey CostGuard limits."""
        pass

class ICaptionService(ABC):
    @abstractmethod
    def generate_captions(self, script: Script, output_path: str) -> str:
        """Generate subtitle file (SRT/ASS) using segment durations (no transcription API)."""
        pass

class IVideoRenderer(ABC):
    @abstractmethod
    def render_video(self, state: VideoState, output_path: str) -> str:
        """Compile audio, video assets, and captions into final MP4."""
        pass

class IYouTubeUploader(ABC):
    @abstractmethod
    def upload_video(self, video_path: str, title: str, description: str, privacy_status: str = "private") -> str:
        """Upload video to YouTube using OAuth2 and return the URL."""
        pass

class IHistoryBackend(ABC):
    @abstractmethod
    def get_recent_topics(self, limit: int = 100) -> List[str]:
        """Retrieve previously used topics."""
        pass

    @abstractmethod
    def record_success(self, topic: str, youtube_url: str):
        """Record a successful upload."""
        pass

    @abstractmethod
    def record_failure(self, topic: str, error_message: str):
        """Record a failed run."""
        pass
