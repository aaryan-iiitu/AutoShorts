import os
import shutil
import tempfile
from contextlib import contextmanager
from core.logger import logger

@contextmanager
def temporary_directory(prefix="autoshorts_"):
    """
    Context manager for creating a deterministic, isolated temporary directory.
    It guarantees cleanup upon exit, even if an exception occurs.
    """
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    logger.debug(f"Created temporary directory: {temp_dir}")
    try:
        yield temp_dir
    finally:
        logger.debug(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)
