"""
Structured logging configuration for the application.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from app.config import LOG_LEVEL, LOG_FORMAT


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in structured JSON format.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON structure.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string with structured log data
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields from record
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "file_path"):
            log_data["file_path"] = record.file_path
            
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Custom formatter for human-readable text output.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as readable text.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted text string
        """
        base_msg = super().format(record)
        
        # Add extra context if available
        extras = []
        if hasattr(record, "job_id"):
            extras.append(f"job_id={record.job_id}")
        if hasattr(record, "status"):
            extras.append(f"status={record.status}")
        if hasattr(record, "duration"):
            extras.append(f"duration={record.duration:.2f}s")
        if hasattr(record, "error_type"):
            extras.append(f"error_type={record.error_type}")
            
        if extras:
            base_msg += f" [{', '.join(extras)}]"
            
        return base_msg


def setup_logging():
    """
    Configure application logging with structured output.
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Set formatter based on config
    if LOG_FORMAT == "json":
        formatter = StructuredFormatter()
    else:
        formatter = TextFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    duration: Optional[float] = None,
    error_type: Optional[str] = None,
    file_path: Optional[str] = None,
    **kwargs
):
    """
    Log a message with structured context.
    
    Args:
        logger: Logger instance
        level: Log level (e.g., logging.INFO)
        message: Log message
        job_id: Job ID for context
        status: Job status
        duration: Duration in seconds
        error_type: Type of error if applicable
        file_path: File path if applicable
        **kwargs: Additional context fields
    """
    extra = {}
    if job_id:
        extra["job_id"] = job_id
    if status:
        extra["status"] = status
    if duration is not None:
        extra["duration"] = duration
    if error_type:
        extra["error_type"] = error_type
    if file_path:
        extra["file_path"] = file_path
    
    # Add any additional kwargs
    extra.update(kwargs)
    
    logger.log(level, message, extra=extra)


# Initialize logging on module import
setup_logging()
