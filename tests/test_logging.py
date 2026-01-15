"""Tests for logging system"""

import pytest
import logging
import tempfile
from pathlib import Path

from docscope.core.logging import setup_logging, get_logger, LogContext


def test_setup_logging_console():
    """Test setting up console logging"""
    setup_logging(level="INFO", console=True)
    
    logger = logging.getLogger()
    assert logger.level == logging.INFO
    
    # Check that console handler is present
    console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert len(console_handlers) > 0


def test_setup_logging_file():
    """Test setting up file logging"""
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
        log_file = f.name
    
    try:
        setup_logging(level="DEBUG", log_file=log_file)
        
        # Write a test message
        logger = logging.getLogger()
        logger.debug("Test message")
        
        # Check that log file exists and contains message
        assert Path(log_file).exists()
        
        with open(log_file) as f:
            content = f.read()
            assert "Test message" in content
    finally:
        Path(log_file).unlink(missing_ok=True)


def test_get_logger():
    """Test getting a named logger"""
    logger = get_logger("test.module")
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


def test_log_levels():
    """Test different log levels"""
    setup_logging(level="WARNING")
    
    logger = logging.getLogger()
    assert logger.level == logging.WARNING
    
    setup_logging(level="ERROR")
    assert logger.level == logging.ERROR
    
    setup_logging(level="DEBUG")
    assert logger.level == logging.DEBUG


def test_log_context():
    """Test LogContext context manager"""
    logger = logging.getLogger()
    original_level = logger.level
    
    with LogContext(level="DEBUG"):
        assert logger.level == logging.DEBUG
    
    # Level should be restored
    assert logger.level == original_level


def test_log_format():
    """Test custom log format"""
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
        log_file = f.name
    
    try:
        custom_format = "%(levelname)s: %(message)s"
        setup_logging(level="INFO", log_file=log_file, log_format=custom_format)
        
        logger = logging.getLogger()
        logger.info("Test message")
        
        with open(log_file) as f:
            content = f.read()
            assert "INFO: Test message" in content
    finally:
        Path(log_file).unlink(missing_ok=True)


def test_rotating_file_handler():
    """Test that rotating file handler is used for file logging"""
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
        log_file = f.name
    
    try:
        setup_logging(log_file=log_file)
        
        logger = logging.getLogger()
        from logging.handlers import RotatingFileHandler
        
        # Check for rotating handler
        rotating_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
        assert len(rotating_handlers) > 0
        
        # Check max bytes setting
        handler = rotating_handlers[0]
        assert handler.maxBytes == 10 * 1024 * 1024  # 10MB
        assert handler.backupCount == 5
    finally:
        Path(log_file).unlink(missing_ok=True)


def test_third_party_log_levels():
    """Test that third-party library log levels are adjusted"""
    setup_logging(level="DEBUG")
    
    # Third-party loggers should be set to WARNING
    uvicorn_logger = logging.getLogger("uvicorn")
    fastapi_logger = logging.getLogger("fastapi")
    
    assert uvicorn_logger.level == logging.WARNING
    assert fastapi_logger.level == logging.WARNING