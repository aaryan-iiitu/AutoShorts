import logging
import sys
from config.settings import settings

class StructuredLogger:
    """
    A lightweight structured logging wrapper around standard Python logging.
    Allows passing arbitrary keyword arguments which are formatted into the log message.
    """
    def __init__(self, name: str = "autoshorts"):
        self._logger = logging.getLogger(name)
        
        # Avoid adding multiple handlers if setup is called multiple times
        if not self._logger.handlers:
            log_level_name = settings.log_level.upper()
            log_level = getattr(logging, log_level_name, logging.INFO)
            self._logger.setLevel(log_level)

            formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S"
            )

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            
            self._logger.addHandler(console_handler)
            self._logger.propagate = False
            
        self.redacted_keys = {"api_key", "token", "secret", "password", "credential", "auth"}

    def _format_kwargs(self, kwargs: dict) -> str:
        if not kwargs:
            return ""
            
        formatted_items = []
        for k, v in kwargs.items():
            # Redact sensitive information
            if any(redact_term in k.lower() for redact_term in self.redacted_keys):
                formatted_items.append(f"{k}='***'")
            else:
                # Basic escaping/formatting for values
                if isinstance(v, str) and (" " in v or '"' in v or "=" in v):
                    val_escaped = v.replace('"', '\\"')
                    formatted_items.append(f'{k}="{val_escaped}"')
                else:
                    formatted_items.append(f"{k}={v}")
                    
        return " [" + " ".join(formatted_items) + "]"

    def debug(self, msg: str, *args, **kwargs):
        self._logger.debug(str(msg) + self._format_kwargs(kwargs), *args)

    def info(self, msg: str, *args, **kwargs):
        self._logger.info(str(msg) + self._format_kwargs(kwargs), *args)

    def warning(self, msg: str, *args, **kwargs):
        self._logger.warning(str(msg) + self._format_kwargs(kwargs), *args)

    def error(self, msg: str, *args, **kwargs):
        self._logger.error(str(msg) + self._format_kwargs(kwargs), *args)

    def exception(self, msg: str, *args, **kwargs):
        # exception() automatically sets exc_info=True
        self._logger.exception(str(msg) + self._format_kwargs(kwargs), *args)
        
    def critical(self, msg: str, *args, **kwargs):
        # Preserve exc_info if it's passed in kwargs, else just format
        exc_info = kwargs.pop("exc_info", None)
        if exc_info is not None:
            self._logger.critical(str(msg) + self._format_kwargs(kwargs), *args, exc_info=exc_info)
        else:
            self._logger.critical(str(msg) + self._format_kwargs(kwargs), *args)

def setup_logger():
    return StructuredLogger("autoshorts")

logger = setup_logger()
