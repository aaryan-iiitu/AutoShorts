from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Groq Settings
    groq_api_key: str = Field(default="", description="Groq API Key for script generation")
    groq_model: str = Field(default="llama3-70b-8192", description="Model to use for script generation")
    
    # Visual Provider Settings
    pexels_api_key: str = Field(default="", description="Pexels API Key for free stock videos/images")
    unsplash_api_key: str = Field(default="", description="Unsplash API Key for fallback stock images")
    
    # YouTube Settings
    youtube_client_secrets_file: str = Field(default="client_secrets.json", description="Path to YouTube client secrets")
    youtube_credentials_file: str = Field(default="youtube_credentials.json", description="Path to save YouTube OAuth credentials")
    
    # Pipeline Settings
    video_width: int = 1080
    video_height: int = 1920
    db_path: str = "autoshorts_history.db"
    log_level: str = "INFO"

    # CostGuard Settings (Strictly Zero-Cost)
    max_runs_per_day: int = Field(default=1, description="Maximum pipeline executions per day")
    max_groq_requests_per_run: int = Field(default=3, description="Max Groq API requests allowed per run")
    max_visual_searches_per_run: int = Field(default=3, description="Max Pexels/Pixabay searches per run")
    max_visual_downloads_per_run: int = Field(default=8, description="Max video/image downloads per run")
    max_retries: int = Field(default=2, description="Max retry attempts for transient network errors")
    network_timeout_seconds: int = Field(default=30, description="Strict network timeout across all APIs")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
