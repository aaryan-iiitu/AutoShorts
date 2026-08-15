import threading
from config.settings import settings
from core.exceptions import CostGuardError
from core.logger import logger

class CostGuard:
    """
    Enforces strict zero-cost limits across the pipeline.
    Ensures that no runaway loops or excessive API calls generate unintended costs.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.groq_requests = 0
        self.visual_searches = 0
        self.visual_downloads = 0

    def increment_groq_requests(self):
        with self.lock:
            if self.groq_requests >= settings.max_groq_requests_per_run:
                logger.error("CostGuard: Max Groq requests exceeded", limit=settings.max_groq_requests_per_run)
                raise CostGuardError(f"Exceeded MAX_GROQ_REQUESTS_PER_RUN ({settings.max_groq_requests_per_run})")
            self.groq_requests += 1

    def increment_visual_searches(self):
        with self.lock:
            if self.visual_searches >= settings.max_visual_searches_per_run:
                logger.error("CostGuard: Max visual searches exceeded", limit=settings.max_visual_searches_per_run)
                raise CostGuardError(f"Exceeded MAX_VISUAL_SEARCHES_PER_RUN ({settings.max_visual_searches_per_run})")
            self.visual_searches += 1

    def increment_visual_downloads(self):
        with self.lock:
            if self.visual_downloads >= settings.max_visual_downloads_per_run:
                logger.error("CostGuard: Max visual downloads exceeded", limit=settings.max_visual_downloads_per_run)
                raise CostGuardError(f"Exceeded MAX_VISUAL_DOWNLOADS_PER_RUN ({settings.max_visual_downloads_per_run})")
            self.visual_downloads += 1

# Singleton instance per run
cost_guard = CostGuard()
