"""
NEMT Python Engine - Electron Log Integration

Provides JSON-formatted log output compatible with Electron's logging system.
Logs are written to stdout in a format that Electron can capture and display.

Format:
{"level": "INFO", "message": "...", "timestamp": "...", "source": "..."}
"""

import json
import logging
import sys
import time
from datetime import datetime
from typing import Optional


class ElectronLogHandler(logging.Handler):
    """
    Logging handler that outputs JSON-formatted logs to stdout.
    
    This handler is designed to work with Electron's log capture system:
    - Output is written to stdout as JSON
    - Each log entry contains: level, message, timestamp, source
    - Flush is called after each write to ensure immediate delivery
    
    Usage:
        handler = ElectronLogHandler()
        handler.setFormatter(ElectronLogFormatter())
        logging.getLogger().addHandler(handler)
    """

    def __init__(self, level: int = logging.INFO):
        super().__init__(level)
        self.flush_interval = 1.0  # Flush every second max
        self._last_flush = time.time()

    def emit(self, record: logging.LogRecord):
        """Emit a log record as JSON to stdout."""
        try:
            log_entry = {
                "level": record.levelname,
                "message": self.format(record),
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "source": record.name,
            }

            # Add extra fields if present
            if hasattr(record, "extra"):
                log_entry.update(record.extra)

            # Write JSON to stdout
            output = json.dumps(log_entry, ensure_ascii=False)
            print(output, flush=True)

            # Periodic flush (already flushed above, but as a safety measure)
            now = time.time()
            if now - self._last_flush > self.flush_interval:
                sys.stdout.flush()
                self._last_flush = now

        except Exception:
            self.handleError(record)

    def flush(self):
        """Flush the output stream."""
        sys.stdout.flush()


class ElectronLogFormatter(logging.Formatter):
    """
    Formatter for Electron-compatible log output.
    
    Formats log records as simple message strings for the JSON handler.
    """

    def __init__(self, fmt: Optional[str] = None):
        super().__init__(fmt)

    def format(self, record: logging.LogRecord) -> str:
        """Format the record as a simple message."""
        if self._fmt:
            return super().format(record)
        
        # Simple format: [LEVEL] source: message
        if record.name and record.name != "root":
            return f"[{record.levelname}] {record.name}: {record.getMessage()}"
        return f"[{record.levelname}] {record.getMessage()}"


class StructuredLogFormatter(logging.Formatter):
    """
    Formatter that adds structured metadata to log messages.
    """

    def __init__(
        self,
        include_module: bool = True,
        include_func: bool = True,
        include_line: bool = False
    ):
        super().__init__()
        self.include_module = include_module
        self.include_func = include_func
        self.include_line = include_line

    def format(self, record: logging.LogRecord) -> str:
        """Format with additional context."""
        parts = [record.getMessage()]

        if self.include_module and record.module:
            parts.append(f"module={record.module}")

        if self.include_func and record.funcName:
            parts.append(f"func={record.funcName}")

        if self.include_line and record.lineno:
            parts.append(f"line={record.lineno}")

        return " | ".join(parts)


def setup_electron_logging(
    level: int = logging.INFO,
    include_source: bool = True
) -> ElectronLogHandler:
    """
    Set up logging compatible with Electron's log capture.
    
    Args:
        level: Logging level (default: INFO)
        include_source: Whether to include logger name in output
        
    Returns:
        The configured ElectronLogHandler
    """
    handler = ElectronLogHandler(level)
    
    if include_source:
        handler.setFormatter(ElectronLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("grpc").setLevel(logging.WARNING)

    return handler


def log_json(level: str, message: str, **kwargs):
    """
    Direct JSON logging function.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        **kwargs: Additional fields to include in the JSON output
    """
    log_entry = {
        "level": level.upper(),
        "message": message,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }
    print(json.dumps(log_entry), flush=True)


# Convenience functions
def log_debug(message: str, **kwargs):
    """Log a debug message."""
    log_json("DEBUG", message, **kwargs)


def log_info(message: str, **kwargs):
    """Log an info message."""
    log_json("INFO", message, **kwargs)


def log_warning(message: str, **kwargs):
    """Log a warning message."""
    log_json("WARNING", message, **kwargs)


def log_error(message: str, **kwargs):
    """Log an error message."""
    log_json("ERROR", message, **kwargs)


def log_critical(message: str, **kwargs):
    """Log a critical message."""
    log_json("CRITICAL", message, **kwargs)
