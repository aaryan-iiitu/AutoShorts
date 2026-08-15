import pytest
from unittest.mock import MagicMock, patch
from services.visual_provider import PexelsUnsplashProvider
from models.domain import Script
from config.settings import settings
from core.exceptions import AssetFetchError

@pytest.fixture(autouse=True)
def setup_config(monkeypatch):
    import core.cost_guard
    core.cost_guard.cost_guard.visual_searches = 0
    core.cost_guard.cost_guard.visual_downloads = 0
    monkeypatch.setattr(settings, "pexels_api_key", "mock")
    monkeypatch.setattr(settings, "unsplash_api_key", "mock")

def test_fetch_assets_pexels_success(mocker, tmp_path):
    provider = PexelsUnsplashProvider()
    
    mock_search_pexels = mocker.patch.object(provider, "_search_pexels", return_value=["http://test.com/vid.mp4"])
    mock_download = mocker.patch.object(provider, "_download_asset", return_value=str(tmp_path / "vid.mp4"))
    
    script = Script(topic="Tech", segments=[])
    assets = provider.fetch_assets(script, 1, str(tmp_path))
    
    assert len(assets) == 1
    mock_search_pexels.assert_called_once()
    mock_download.assert_called_once()

def test_fetch_assets_fallback(mocker, tmp_path):
    provider = PexelsUnsplashProvider()
    
    mocker.patch.object(provider, "_search_pexels", return_value=[])
    mocker.patch.object(provider, "_search_unsplash", return_value=[])
    mock_fallback = mocker.patch.object(provider, "_get_local_fallback", return_value=str(tmp_path / "fallback.mp4"))
    
    script = Script(topic="Tech", segments=[])
    assets = provider.fetch_assets(script, 1, str(tmp_path))
    
    assert len(assets) == 1
    mock_fallback.assert_called_once()

def test_fetch_assets_no_fallback_raises(mocker, tmp_path):
    provider = PexelsUnsplashProvider()
    
    mocker.patch.object(provider, "_search_pexels", return_value=[])
    mocker.patch.object(provider, "_search_unsplash", return_value=[])
    mocker.patch.object(provider, "_get_local_fallback", return_value="")
    
    script = Script(topic="Tech", segments=[])
    
    with pytest.raises(AssetFetchError):
        provider.fetch_assets(script, 1, str(tmp_path))
