import pytest
import os
from unittest.mock import patch, MagicMock
from services.video_renderer import FFmpegRenderer
from models.domain import VideoState, VideoAsset
from core.exceptions import RenderingError

def test_renderer_missing_assets():
    renderer = FFmpegRenderer()
    state = VideoState(topic="Test")
    
    with pytest.raises(RenderingError, match="No visual assets"):
        renderer.render_video(state, "out.mp4")

def test_renderer_missing_audio(tmp_path):
    renderer = FFmpegRenderer()
    state = VideoState(
        topic="Test",
        assets=[VideoAsset(filepath="test.mp4", description="test")]
    )
    
    with pytest.raises(RenderingError, match="Narration audio is missing"):
        renderer.render_video(state, "out.mp4")

@patch("services.video_renderer.subprocess.run")
def test_renderer_success(mock_run, tmp_path):
    # Mock file existences
    audio_path = tmp_path / "audio.mp3"
    audio_path.touch()
    
    srt_path = tmp_path / "captions.srt"
    srt_path.touch()
    
    out_path = tmp_path / "out.mp4"
    
    # We must mock os.path.exists for the output file check to pass
    original_exists = os.path.exists
    def mock_exists(path):
        if str(path) == str(out_path): return True
        return original_exists(path)
        
    state = VideoState(
        topic="Test",
        assets=[VideoAsset(filepath="test1.mp4", description="test"), VideoAsset(filepath="test2.mp4", description="test")],
        audio_path=str(audio_path)
    )
    
    renderer = FFmpegRenderer()
    
    with patch("os.path.exists", side_effect=mock_exists):
        renderer.render_video(state, str(out_path))
        
    mock_run.assert_called_once()
    
    cmd_args = mock_run.call_args[0][0]
    assert "ffmpeg" in cmd_args
    assert "-c:v" in cmd_args
    assert "libx264" in cmd_args
    assert "-shortest" in cmd_args
