from pydantic import BaseModel
from typing import List, Optional

class ScriptSegment(BaseModel):
    """Represents a single narration segment of the script."""
    text: str
    audio_path: Optional[str] = None
    duration: float = 0.0  # Duration of the generated audio in seconds

class Script(BaseModel):
    """The generated script containing multiple narration segments."""
    topic: str
    segments: List[ScriptSegment]
    
    @property
    def full_text(self) -> str:
        return " ".join(s.text for s in self.segments)

class VideoAsset(BaseModel):
    """Represents a downloaded visual asset."""
    filepath: str
    description: str

class VideoState(BaseModel):
    """Holds the overall state of a single pipeline run."""
    topic: str
    script: Optional[Script] = None
    assets: List[VideoAsset] = []
    final_video_path: Optional[str] = None
    youtube_url: Optional[str] = None
