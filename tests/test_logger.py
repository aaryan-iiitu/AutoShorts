import pytest
import logging
from unittest.mock import patch, MagicMock
from core.logger import StructuredLogger

@pytest.fixture
def capture_logger():
    # Helper to capture log output
    logger_instance = StructuredLogger("test_logger")
    # Add a handler just for capturing
    log_handler = logging.StreamHandler()
    log_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(message)s")
    log_handler.setFormatter(formatter)
    
    # We clear handlers and add ours to isolate the test
    logger_instance._logger.handlers.clear()
    logger_instance._logger.addHandler(log_handler)
    logger_instance._logger.setLevel(logging.DEBUG)
    
    return logger_instance, log_handler

def test_logger_info(capture_logger, caplog):
    logger, _ = capture_logger
    logger.info("test", channel="technology")
    
    assert "test [channel=technology]" in caplog.text

def test_logger_warning(capture_logger, caplog):
    logger, _ = capture_logger
    logger.warning("test", retry=2)
    
    assert "test [retry=2]" in caplog.text

def test_logger_error(capture_logger, caplog):
    logger, _ = capture_logger
    logger.error("test", provider="pexels")
    
    assert "test [provider=pexels]" in caplog.text

def test_logger_exception(capture_logger, caplog):
    logger, _ = capture_logger
    try:
        raise ValueError("Oops")
    except ValueError:
        logger.exception("test", error="example")
        
    assert "test [error=example]" in caplog.text
    assert "ValueError: Oops" in caplog.text
    assert "Traceback" in caplog.text

def test_logger_redaction(capture_logger, caplog):
    logger, _ = capture_logger
    logger.info("Auth event", pexels_api_key="secret123", token="abc", some_value="ok")
    
    assert "pexels_api_key='***'" in caplog.text
    assert "token='***'" in caplog.text
    assert "some_value=ok" in caplog.text
    assert "secret123" not in caplog.text
    assert "abc" not in caplog.text
    
def test_logger_critical_exc_info(capture_logger, caplog):
    logger, _ = capture_logger
    try:
        raise RuntimeError("Critical issue")
    except RuntimeError:
        logger.critical("Pipeline stopped", error="runtime", exc_info=True)
        
    assert "Pipeline stopped [error=runtime]" in caplog.text
    assert "RuntimeError: Critical issue" in caplog.text
