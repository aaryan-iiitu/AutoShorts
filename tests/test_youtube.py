import pytest
from unittest.mock import patch, MagicMock
from services.youtube_uploader import YouTubeUploader
from core.exceptions import UploadError
from config.settings import settings

@patch("services.youtube_uploader.os.path.exists")
def test_uploader_missing_creds(mock_exists):
    mock_exists.return_value = False
    uploader = YouTubeUploader()
    with pytest.raises(UploadError, match="Missing YouTube credentials"):
        uploader.upload_video("test.mp4", "Title", "Desc")

@patch("services.youtube_uploader.build")
@patch("services.youtube_uploader.os.path.exists")
@patch("builtins.open", new_callable=MagicMock)
def test_uploader_success(mock_open, mock_exists, mock_build, mocker):
    mock_exists.return_value = True
    
    # Mock JSON load
    mocker.patch("services.youtube_uploader.json.load", return_value={"refresh_token": "mock"})
    
    # Mock Google API Builder
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    mock_request = MagicMock()
    mock_youtube.videos().insert.return_value = mock_request
    mock_request.execute.return_value = {"id": "abcdef12345"}
    
    # Mock MediaFileUpload
    mocker.patch("services.youtube_uploader.MediaFileUpload", return_value="mock_media")
    
    uploader = YouTubeUploader()
    url = uploader.upload_video("test.mp4", "My Video", "Description", "private")
    
    assert url == "https://www.youtube.com/shorts/abcdef12345"
    mock_youtube.videos().insert.assert_called_once()
