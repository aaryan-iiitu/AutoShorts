import pytest
from unittest.mock import MagicMock, patch
from core.orchestrator import Orchestrator
from models.domain import Script, ScriptSegment

def test_orchestrator_dry_run(mocker):
    # Mock dependencies
    topic_gen = MagicMock()
    script_gen = MagicMock()
    tts = MagicMock()
    visual = MagicMock()
    caption = MagicMock()
    renderer = MagicMock()
    uploader = MagicMock()
    history = MagicMock()
    
    orchestrator = Orchestrator(
        topic_gen, script_gen, tts, visual, caption, renderer, uploader, history
    )
    
    orchestrator.run(dry_run=True)
    
    # History is called, but external APIs are skipped
    history.get_recent_topics.assert_called_once()
    topic_gen.generate_topic.assert_not_called()
    script_gen.generate_script.assert_not_called()
    uploader.upload_video.assert_not_called()

@patch("core.orchestrator.subprocess.run")
def test_orchestrator_full_flow(mock_run, mocker, tmp_path):
    topic_gen = MagicMock()
    topic_gen.generate_topic.return_value = "Test Topic"
    
    script_gen = MagicMock()
    script_gen.generate_script.return_value = Script(topic="Test Topic", segments=[ScriptSegment(text="Hello", duration=1.0)])
    
    tts = MagicMock()
    tts.generate_audio.return_value = 1.0
    
    visual = MagicMock()
    visual.fetch_assets.return_value = ["vid1.mp4"]
    
    caption = MagicMock()
    renderer = MagicMock()
    uploader = MagicMock()
    history = MagicMock()
    
    orchestrator = Orchestrator(
        topic_gen, script_gen, tts, visual, caption, renderer, uploader, history
    )
    
    # We must mock os.path.exists and getsize for validation
    mocker.patch("core.orchestrator.os.path.exists", return_value=True)
    mocker.patch("core.orchestrator.os.path.getsize", return_value=5000)
    
    orchestrator.run(upload=False)
    
    topic_gen.generate_topic.assert_called_once()
    script_gen.generate_script.assert_called_once()
    tts.generate_audio.assert_called_once()
    caption.generate_captions.assert_called_once()
    visual.fetch_assets.assert_called_once()
    renderer.render_video.assert_called_once()
    
    # Should not upload because upload=False
    uploader.upload_video.assert_not_called()
    # Should not record success if upload was intentionally skipped (Wait, should it? 
    # Current code records success only if upload=True, which is correct because it wasn't published)
    history.record_success.assert_not_called()
