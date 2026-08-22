from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception, retry_if_exception_type, before_sleep_log
import logging
from config.settings import settings
from core.exceptions import QuotaExceededError, CostGuardError
from core.logger import logger

def is_retryable(exception: Exception) -> bool:
    """Determine if we should retry based on the exception type."""
    if isinstance(exception, (QuotaExceededError, CostGuardError)):
        # Do not retry if we strictly know it's a hard quota limit or CostGuard breach
        return False
    return True

def api_retry():
    """
    Exponential backoff retry decorator for external API calls.
    Respects CostGuard MAX_RETRIES.
    """
    # Grab the standard logger for tenacity
    stdlib_logger = logging.getLogger("api_retry")
    
    return retry(
        wait=wait_exponential(multiplier=2, min=2, max=10),
        stop=stop_after_attempt(settings.max_retries + 1),  # stop_after_attempt counts the initial try + retries
        retry=retry_if_exception_type(Exception) & retry_if_exception(is_retryable),
        before_sleep=before_sleep_log(stdlib_logger, logging.WARNING),
        reraise=True
    )
