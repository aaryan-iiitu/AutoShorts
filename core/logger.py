import logging
import sys
from config.settings import settings

def setup_logger():
    """Configure standard Python logging for the application."""
    logger = logging.getLogger("autoshorts")
    
    # Avoid adding multiple handlers if setup is called multiple times
    if logger.handlers:
        return logger

    log_level_name = settings.log_level.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # Do not propagate to root logger
    logger.propagate = False
    
    return logger

logger = setup_logger()
