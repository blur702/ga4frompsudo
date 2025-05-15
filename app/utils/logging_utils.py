"""
Logging utility functions and configuration.
Provides consistent logging setup across the application.
"""

import os
import logging
import logging.handlers
import datetime
from typing import Optional

def configure_logging(app_name: str = 'ga4_dashboard', 
                     log_level: Optional[str] = None,
                     log_file: Optional[str] = None,
                     log_to_console: bool = True,
                     file_log_level: str = "ERROR",
                     clear_log_file: bool = True) -> logging.Logger:
    """
    Configure application-wide logging with consistent formatting.
    
    Args:
        app_name (str): Name of the application (used as logger name)
        log_level (str, optional): Logging level for console (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                                  If None, uses LOG_LEVEL environment variable or defaults to INFO
        log_file (str, optional): Path to log file. If None, logs to console only.
        log_to_console (bool): Whether to also log to console when log_file is specified
        file_log_level (str): Minimum level for log file entries (defaults to ERROR only)
        clear_log_file (bool): Whether to clear the log file on startup (defaults to True)
        
    Returns:
        logging.Logger: The configured root logger
    """
    # Determine log level
    if log_level is None:
        log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    else:
        log_level_str = log_level.upper()
        
    # Convert string levels to logging constants
    numeric_level = getattr(logging, log_level_str, logging.INFO)
    file_numeric_level = getattr(logging, file_log_level.upper(), logging.ERROR)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(min(numeric_level, file_numeric_level))  # Set to the most verbose level needed
    
    # Clear any existing handlers (to avoid duplicate logging)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    
    # Define log format
    log_format = '%(asctime)s %(levelname)s %(name)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(log_format, date_format)
    
    # Add file handler if log_file is specified
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Clear the log file if requested
        if clear_log_file and os.path.exists(log_file):
            open(log_file, 'w').close()  # Truncate the file
            
        # Use a file handler with ERROR level only
        file_handler = logging.FileHandler(
            filename=log_file,
            encoding='utf-8',
            mode='a'  # Append mode
        )
        file_handler.setLevel(file_numeric_level)  # Set to ERROR or specified level
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Log run separator
        run_separator = f"\n{'='*80}\nAPPLICATION RUN: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*80}\n"
        with open(log_file, 'a') as f:
            f.write(run_separator)
    
    # Add console handler if log_to_console is True or no log_file specified
    if log_to_console or not log_file:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)  # Use configured console level
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Log initial message
    logger.info(f"Logging configured for {app_name}: console level={log_level_str}, " 
               f"file level={file_log_level if log_file else 'N/A'}")
    return logger

def log_exception(logger: logging.Logger, exception: Exception, 
                  message: str = "An exception occurred", 
                  level: int = logging.ERROR) -> None:
    """
    Log an exception with complete traceback and context.
    
    Args:
        logger (logging.Logger): The logger to use
        exception (Exception): The exception object to log
        message (str): An additional message to include
        level (int): The logging level to use (default: ERROR)
    """
    logger.log(level, f"{message}: {str(exception)}", exc_info=True)

def create_audit_log(action: str, user_id: Optional[str] = None, 
                    resource_id: Optional[str] = None, 
                    details: Optional[dict] = None) -> dict:
    """
    Create a structured audit log entry for security events.
    
    Args:
        action (str): The action being performed (e.g., 'login', 'data_access')
        user_id (str, optional): Identifier for the user performing the action
        resource_id (str, optional): Identifier for the resource being accessed
        details (dict, optional): Additional context about the action
        
    Returns:
        dict: Structured audit log entry
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    audit_entry = {
        'timestamp': timestamp,
        'action': action,
        'user_id': user_id,
        'resource_id': resource_id,
        'details': details or {}
    }
    
    # Get the logger for audit events
    audit_logger = logging.getLogger('audit')
    audit_logger.info(f"AUDIT: {audit_entry}")
    
    return audit_entry