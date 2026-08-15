import pytest
from unittest.mock import MagicMock, AsyncMock
from services.tts_service import EdgeTTSService
from core.exceptions import GenerationError

def test_tts_service_success(mocker, tmp_path):
    output_file = str(tmp_path / "test.mp3")
    
    # Mock Edge TTS
    mock_communicate_cls = mocker.patch("services.tts_service.edge_tts.Communicate")
    mock_communicate = MagicMock()
    mock_communicate.save = AsyncMock()
    mock_communicate_cls.return_value = mock_communicate
    
    # Mock subprocess.run for ffprobe
    mock_subprocess = mocker.patch("services.tts_service.subprocess.run")
    mock_result = MagicMock()
    mock_result.stdout = "2.55\n"
    mock_subprocess.return_value = mock_result
    
    tts = EdgeTTSService()
    duration = tts.generate_audio("Hello world", output_file)
    
    assert duration == 2.55
    mock_communicate_cls.assert_called_once_with("Hello world", "en-US-ChristopherNeural")
    mock_communicate.save.assert_called_once_with(output_file)
    mock_subprocess.assert_called_once()

def test_tts_service_ffprobe_failure(mocker, tmp_path):
    output_file = str(tmp_path / "test.mp3")
    
    mocker.patch("services.tts_service.edge_tts.Communicate", return_value=MagicMock(save=AsyncMock()))
    
    import subprocess
    mock_subprocess = mocker.patch("services.tts_service.subprocess.run")
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "ffprobe", stderr="file not found")
    
    tts = EdgeTTSService()
    
    with pytest.raises(GenerationError) as exc:
        tts.generate_audio("Hello world", output_file)
    
    assert "FFprobe failed" in str(exc.value)
