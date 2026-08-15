class AutoShortsError(Exception):
    """Base exception for all AutoShorts errors."""
    pass

class CostGuardError(AutoShortsError):
    """Raised when CostGuard detects a hard limit breach."""
    pass

class QuotaExceededError(AutoShortsError):
    """Raised when an API free tier limit or quota is reached."""
    pass

class GenerationError(AutoShortsError):
    """Raised when script or topic generation fails."""
    pass

class AssetFetchError(AutoShortsError):
    """Raised when fetching external assets (video/audio) fails."""
    pass

class RenderingError(AutoShortsError):
    """Raised when FFmpeg rendering fails."""
    pass

class UploadError(AutoShortsError):
    """Raised when YouTube upload fails."""
    pass
