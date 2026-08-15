from config.settings import settings

def test_default_settings():
    """Ensure that the default settings load correctly and enforce zero-cost values."""
    assert settings.max_runs_per_day == 1
    assert settings.max_groq_requests_per_run == 3
    assert settings.max_visual_searches_per_run == 3
    assert settings.max_visual_downloads_per_run == 8
    assert settings.max_retries == 2
    assert settings.network_timeout_seconds == 30
    assert settings.log_level in ["INFO", "DEBUG", "WARNING", "ERROR"]
