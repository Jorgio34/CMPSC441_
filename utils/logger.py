"""
Logging Utility Module

This module provides logging functionality for the D&D AI Assistant.
It configures logging with appropriate formats and handlers for different
environments (console, file, etc.) and offers utility functions for logging.
"""

import os
import sys
import logging
import datetime
from typing import Optional, Dict, Any, Union, List

# Default log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

# Create logs directory if it doesn't exist
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except Exception as e:
        print(f"Warning: Could not create log directory: {e}")
        LOG_DIR = os.path.dirname(os.path.dirname(__file__))

# Define log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# Define log levels with their integer values
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,        # 10
    "INFO": logging.INFO,          # 20
    "WARNING": logging.WARNING,    # 30
    "ERROR": logging.ERROR,        # 40
    "CRITICAL": logging.CRITICAL   # 50
}

# Global logger dictionary to keep track of initialized loggers
_loggers = {}


def get_logger(name: str, 
               level: str = "INFO",
               log_to_console: bool = True,
               log_to_file: bool = True,
               log_format: str = DEFAULT_LOG_FORMAT,
               log_file: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with the specified name and configuration.
    
    Args:
        name: Name of the logger
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        log_format: Format string for log messages
        log_file: Custom log file name (if None, uses name_YYYY-MM-DD.log)
        
    Returns:
        Configured logger instance
    """
    # Check if logger already exists
    if name in _loggers:
        return _loggers[name]
        
    # Create new logger
    logger = logging.getLogger(name)
    
    # Set log level
    level = level.upper()
    if level not in LOG_LEVELS:
        print(f"Warning: Invalid log level '{level}'. Using INFO instead.")
        level = "INFO"
    
    logger.setLevel(LOG_LEVELS[level])
    
    # Prevent adding handlers if logger already has them
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # Create formatters
    formatter = logging.Formatter(log_format)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        if log_file is None:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            log_file = f"{name}_{today}.log"
        
        try:
            file_handler = logging.FileHandler(os.path.join(LOG_DIR, log_file))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not create log file handler: {e}")
    
    # Store logger in global dictionary
    _loggers[name] = logger
    
    return logger


def setup_root_logger(level: str = "INFO",
                      log_to_console: bool = True,
                      log_to_file: bool = True,
                      log_format: str = DETAILED_LOG_FORMAT) -> logging.Logger:
    """
    Set up the root logger for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        log_format: Format string for log messages
        
    Returns:
        Configured root logger
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = f"dnd_assistant_{today}.log"
    
    return get_logger("dnd_assistant", level, log_to_console, log_to_file, log_format, log_file)


def log_function_call(logger: logging.Logger, func_name: str, args: Dict[str, Any]) -> None:
    """
    Log a function call with its arguments.
    
    Args:
        logger: Logger instance to use
        func_name: Name of the function being called
        args: Dictionary of function arguments
    """
    # Sanitize arguments for logging (remove sensitive data if needed)
    safe_args = {k: v for k, v in args.items() if not k.lower() in ["api_key", "password", "token", "secret"]}
    
    logger.debug(f"Function call: {func_name} - Args: {safe_args}")


def log_api_request(logger: logging.Logger, 
                   service: str, 
                   endpoint: str, 
                   method: str = "GET",
                   params: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an API request.
    
    Args:
        logger: Logger instance to use
        service: Name of the API service
        endpoint: API endpoint being accessed
        method: HTTP method (GET, POST, etc.)
        params: Request parameters (sanitized for logging)
    """
    if params:
        # Sanitize parameters to remove sensitive information
        safe_params = {k: v for k, v in params.items() if not k.lower() in ["api_key", "password", "token", "secret"]}
        logger.info(f"API Request: {method} {service}/{endpoint} - Params: {safe_params}")
    else:
        logger.info(f"API Request: {method} {service}/{endpoint}")


def log_error(logger: logging.Logger, 
             error: Exception, 
             context: Optional[str] = None) -> None:
    """
    Log an error with context and exception details.
    
    Args:
        logger: Logger instance to use
        error: Exception that occurred
        context: Additional context information
    """
    if context:
        logger.error(f"{context} - Error: {type(error).__name__}: {str(error)}")
    else:
        logger.error(f"Error: {type(error).__name__}: {str(error)}")
    
    # For debugging, also log the stack trace
    if logger.level <= logging.DEBUG:
        import traceback
        logger.debug(f"Stack trace: {''.join(traceback.format_tb(error.__traceback__))}")


def log_game_event(logger: logging.Logger, 
                  event_type: str, 
                  details: Union[str, Dict[str, Any]],
                  session_id: Optional[str] = None) -> None:
    """
    Log a game event.
    
    Args:
        logger: Logger instance to use
        event_type: Type of game event (combat, dialogue, quest, etc.)
        details: Event details as string or dictionary
        session_id: Optional session identifier
    """
    if session_id:
        if isinstance(details, dict):
            logger.info(f"Game Event [{session_id}] - {event_type}: {details}")
        else:
            logger.info(f"Game Event [{session_id}] - {event_type}: {details}")
    else:
        if isinstance(details, dict):
            logger.info(f"Game Event - {event_type}: {details}")
        else:
            logger.info(f"Game Event - {event_type}: {details}")


def log_llm_interaction(logger: logging.Logger, 
                        prompt_type: str,
                        inputs: Optional[Dict[str, Any]] = None,
                        tokens_used: Optional[int] = None,
                        model: Optional[str] = None) -> None:
    """
    Log an interaction with a language model.
    
    Args:
        logger: Logger instance to use
        prompt_type: Type of prompt (quest generation, NPC dialogue, etc.)
        inputs: Input parameters (sanitized)
        tokens_used: Number of tokens used in the interaction
        model: Name of the language model used
    """
    log_parts = [f"LLM Interaction - {prompt_type}"]
    
    if model:
        log_parts.append(f"Model: {model}")
    
    if tokens_used:
        log_parts.append(f"Tokens: {tokens_used}")
    
    if inputs:
        # Sanitize inputs to remove lengthy content or sensitive data
        safe_inputs = {}
        for k, v in inputs.items():
            if isinstance(v, str) and len(v) > 100:
                safe_inputs[k] = f"{v[:100]}... [truncated, total length: {len(v)}]"
            elif not k.lower() in ["api_key", "password", "token", "secret"]:
                safe_inputs[k] = v
                
        log_parts.append(f"Inputs: {safe_inputs}")
    
    logger.info(" | ".join(log_parts))


def get_all_loggers() -> List[logging.Logger]:
    """
    Get all configured loggers.
    
    Returns:
        List of all logger instances
    """
    return list(_loggers.values())


def set_all_loggers_level(level: str) -> None:
    """
    Set the level for all configured loggers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = level.upper()
    if level not in LOG_LEVELS:
        print(f"Warning: Invalid log level '{level}'. Using INFO instead.")
        level = "INFO"
    
    log_level = LOG_LEVELS[level]
    
    for logger in _loggers.values():
        logger.setLevel(log_level)

def setup_logging(level="INFO", log_to_file=True, log_filename=None, debug=False):
    """
    Set up the logging system for the D&D AI Assistant.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_filename: Custom log file name (if None, uses default name)
        debug: If True, set log level to DEBUG regardless of level parameter
        
    Returns:
        Configured root logger
    """
    # Set level to DEBUG if debug flag is True
    if debug:
        level = "DEBUG"
    
    # Set up the root logger
    root_logger = setup_root_logger(
        level=level,
        log_to_console=True,
        log_to_file=log_to_file
    )
    
    # Set log level on all existing loggers
    set_all_loggers_level(level)
    
    logger.info(f"Logging system initialized at level {level}")
    
    return root_logger
# Create default logger for this module
logger = setup_root_logger()

# Log module initialization
logger.debug("Logger module initialized")