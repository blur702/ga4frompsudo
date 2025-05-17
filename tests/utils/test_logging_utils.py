"""
Unit tests for logging_utils module.
Tests logging configuration and utility functions.
"""

import os
import logging
import pytest
import tempfile
from app.utils.logging_utils import (
    configure_logging,
    log_exception,
    create_audit_log
)

class TestLoggingUtils:
    """Tests for the logging_utils module."""
    
    def test_configure_logging_console_only(self):
        """Test configuring logging with console output only."""
        logger = configure_logging(app_name='test_app', log_file=None, log_to_console=True)
        
        # Verify logger is properly configured
        assert logger.level <= logging.INFO
        
        # Check that we have a console handler
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0
        
        # No file handlers should be present
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0
    
    def test_configure_logging_with_file(self):
        """Test configuring logging with file output."""
        # Use a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            log_path = temp_file.name
        
        try:
            logger = configure_logging(
                app_name='test_app', 
                log_file=log_path, 
                log_to_console=False,
                file_log_level='ERROR',  # Only log errors and above to file
                clear_log_file=True
            )
            
            # Check that we have a file handler
            file_handlers = [h for h in logger.handlers 
                           if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
            
            # Verify the file handler points to our temp file
            assert any(h.baseFilename == log_path for h in file_handlers)
            
            # Verify file handler is only logging ERROR and above
            assert all(h.level == logging.ERROR for h in file_handlers)
            
            # No console handlers should be present if log_to_console=False
            console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)
                               and not isinstance(h, logging.FileHandler)]
            assert len(console_handlers) == 0
            
            # Test writing to the log - INFO level should not be written to file
            info_message = "Test info message"
            logger.info(info_message)
            
            # ERROR level should be written to file
            error_message = "Test error message"
            logger.error(error_message)
            
            # Verify only error message was written to the file
            with open(log_path, 'r') as f:
                log_content = f.read()
                assert error_message in log_content
                assert info_message not in log_content
            
        finally:
            # Clean up the temporary file
            if os.path.exists(log_path):
                os.unlink(log_path)
    
    def test_log_exception(self):
        """Test logging exceptions."""
        # Setup a test logger with a memory handler
        logger = logging.getLogger('test_exception_logger')
        logger.setLevel(logging.DEBUG)
        
        class MemoryHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []
                
            def emit(self, record):
                self.records.append(record)
                
        memory_handler = MemoryHandler()
        logger.addHandler(memory_handler)
        
        # Log an exception
        test_exception = ValueError("Test exception")
        test_message = "Exception occurred during test"
        
        try:
            raise test_exception
        except ValueError as e:
            log_exception(logger, e, test_message)
        
        # Verify the exception was logged correctly
        assert len(memory_handler.records) > 0
        record = memory_handler.records[0]
        
        assert test_message in record.getMessage()
        assert "Test exception" in record.getMessage()
        assert record.exc_info is not None
    
    def test_create_audit_log(self):
        """Test creating audit log entries."""
        # Setup a test logger
        audit_logger = logging.getLogger('audit')
        audit_logger.setLevel(logging.DEBUG)
        
        class MemoryHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []
                
            def emit(self, record):
                self.records.append(record)
                
        memory_handler = MemoryHandler()
        audit_logger.addHandler(memory_handler)
        
        # Create an audit log entry
        action = "user_login"
        user_id = "test_user"
        resource_id = "auth_system"
        details = {"ip": "127.0.0.1", "success": True}
        
        audit_entry = create_audit_log(action, user_id, resource_id, details)
        
        # Verify the audit log entry structure
        assert audit_entry["action"] == action
        assert audit_entry["user_id"] == user_id
        assert audit_entry["resource_id"] == resource_id
        assert audit_entry["details"] == details
        assert "timestamp" in audit_entry
        
        # Verify it was logged
        assert len(memory_handler.records) > 0
        assert "AUDIT" in memory_handler.records[0].getMessage()
        assert action in memory_handler.records[0].getMessage()