"""Logging configuration and utilities."""
import logging
import logging.config
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pythonjsonlogger import jsonlogger

from app.core.config import settings


class RequestIdFilter(logging.Filter):
    """Add request_id to log records."""
    
    def __init__(self, name: str = "", default_request_id: str = "-") -> None:
        """Initialize the filter."""
        super().__init__(name)
        self.default_request_id = default_request_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to the log record."""
        if not hasattr(record, 'request_id'):
            record.request_id = self.default_request_id
        return True


class JsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(
        self, 
        log_record: Dict[str, Any], 
        record: logging.LogRecord, 
        message_dict: Dict[str, Any]
    ) -> None:
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)
        
        if not log_record.get('timestamp'):
            log_record['timestamp'] = self.formatTime(record, self.datefmt)
        
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        if record.name == 'uvicorn.error':
            # Skip adding duplicate fields for uvicorn logs
            return
            
        # Add additional fields
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        log_record['process'] = record.process
        log_record['thread'] = record.thread
        log_record['thread_name'] = record.threadName
        
        # Add exception info if present
        if record.exc_info and not log_record.get('exc_info'):
            log_record['exc_info'] = self.formatException(record.exc_info)
        
        # Add stack info if present
        if record.stack_info and not log_record.get('stack_info'):
            log_record['stack_info'] = self.formatStack(record.stack_info)


def configure_logging() -> None:
    """Configure logging for the application."""
    log_level = settings.LOG_LEVEL.upper()
    log_format = settings.LOG_FORMAT
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Log file paths
    log_file = logs_dir / "app.log"
    error_log_file = logs_dir / "error.log"
    
    # Clear log files if they get too large (10MB)
    max_log_size = 10 * 1024 * 1024  # 10MB
    
    for log_path in [log_file, error_log_file]:
        if log_path.exists() and log_path.stat().st_size > max_log_size:
            log_path.unlink()
    
    # Define log handlers
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "json" if settings.ENVIRONMENT != "development" else "console",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json",
            "filename": str(log_file),
            "maxBytes": max_log_size,
            "backupCount": 5,
            "encoding": "utf8",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json",
            "filename": str(error_log_file),
            "maxBytes": max_log_size,
            "backupCount": 5,
            "encoding": "utf8",
        },
    }
    
    # Define loggers
    loggers = {
        "": {
            "handlers": ["console", "file", "error_file"],
            "level": log_level,
            "propagate": True,
        },
        "app": {
            "handlers": ["console", "file", "error_file"],
            "level": log_level,
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": log_level,
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "file"],
            "level": log_level,
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console", "file"],
            "level": log_level,
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "fastapi": {
            "handlers": ["console", "file"],
            "level": log_level,
            "propagate": False,
        },
    }
    
    # Configure logging
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {
                    "()": RequestIdFilter,
                    "default_request_id": "-",
                },
            },
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%SZ",
                },
                "console": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": handlers,
            "loggers": loggers,
        }
    )
    
    # Set log levels for libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("s3transfer").setLevel(logging.WARNING)
    logging.getLogger("aiobotocore").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aio_pika").setLevel(logging.WARNING)
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
    logging.getLogger("databases").setLevel(logging.INFO)
    logging.getLogger("aioredis").setLevel(logging.INFO)
    logging.getLogger("redis").setLevel(logging.INFO)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("kombu").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.error").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)
    logging.getLogger("starlette").setLevel(log_level)
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Add request ID filter to all handlers
    for handler in root_logger.handlers:
        handler.addFilter(RequestIdFilter())
    
    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info("Logging configured")
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Log level: %s", log_level)
    logger.info("Debug mode: %s", settings.DEBUG)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name. If None, returns the root logger.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    return logger


# Initialize logging when the module is imported
configure_logging()
