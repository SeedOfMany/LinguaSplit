"""
Thread-safe logging system for LinguaSplit GUI.
Provides logging with message queue for GUI display.
"""

import logging
import queue
import threading
from datetime import datetime
from enum import Enum
from typing import Optional, Callable


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class GUILogger:
    """
    Thread-safe logger for GUI applications.

    Features:
    - Message queue for GUI display
    - Multiple log levels
    - Thread-safe operations
    - Optional callback for real-time updates
    """

    def __init__(
        self,
        name: str = "LinguaSplit",
        level: LogLevel = LogLevel.INFO,
        max_queue_size: int = 1000,
        log_to_file: bool = False,
        log_file: Optional[str] = None
    ):
        """
        Initialize GUI logger.

        Args:
            name: Logger name
            level: Minimum log level
            max_queue_size: Maximum queue size
            log_to_file: Whether to log to file
            log_file: Log file path
        """
        self.name = name
        self.level = level
        self.message_queue = queue.Queue(maxsize=max_queue_size)
        self.lock = threading.Lock()
        self.callback: Optional[Callable] = None

        # Create standard logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level.value)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level.value)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Add file handler if requested
        if log_to_file and log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(level.value)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Failed to create log file: {e}")

    def set_callback(self, callback: Callable[[str, str], None]):
        """
        Set callback function for real-time log updates.

        Args:
            callback: Function that takes (level, message) as arguments
        """
        with self.lock:
            self.callback = callback

    def debug(self, message: str):
        """
        Log debug message.

        Args:
            message: Message to log
        """
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str):
        """
        Log info message.

        Args:
            message: Message to log
        """
        self._log(LogLevel.INFO, message)

    def warning(self, message: str):
        """
        Log warning message.

        Args:
            message: Message to log
        """
        self._log(LogLevel.WARNING, message)

    def error(self, message: str):
        """
        Log error message.

        Args:
            message: Message to log
        """
        self._log(LogLevel.ERROR, message)

    def critical(self, message: str):
        """
        Log critical message.

        Args:
            message: Message to log
        """
        self._log(LogLevel.CRITICAL, message)

    def _log(self, level: LogLevel, message: str):
        """
        Internal logging method.

        Args:
            level: Log level
            message: Message to log
        """
        # Check if level is enabled
        if level.value < self.level.value:
            return

        # Create log entry
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'level': level.name,
            'message': message
        }

        # Add to queue (thread-safe)
        try:
            self.message_queue.put_nowait(log_entry)
        except queue.Full:
            # Remove oldest message and add new one
            try:
                self.message_queue.get_nowait()
                self.message_queue.put_nowait(log_entry)
            except queue.Empty:
                pass

        # Log to standard logger
        log_method = getattr(self.logger, level.name.lower())
        log_method(message)

        # Call callback if set
        with self.lock:
            if self.callback:
                try:
                    self.callback(level.name, message)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")

    def get_messages(self, max_count: Optional[int] = None) -> list:
        """
        Get messages from queue.

        Args:
            max_count: Maximum number of messages to retrieve

        Returns:
            List of log entries (dicts with timestamp, level, message)
        """
        messages = []
        count = 0

        while not self.message_queue.empty():
            if max_count and count >= max_count:
                break

            try:
                message = self.message_queue.get_nowait()
                messages.append(message)
                count += 1
            except queue.Empty:
                break

        return messages

    def clear(self):
        """Clear the message queue."""
        with self.lock:
            while not self.message_queue.empty():
                try:
                    self.message_queue.get_nowait()
                except queue.Empty:
                    break

    def set_level(self, level: LogLevel):
        """
        Set minimum log level.

        Args:
            level: New log level
        """
        with self.lock:
            self.level = level
            self.logger.setLevel(level.value)
            for handler in self.logger.handlers:
                handler.setLevel(level.value)

    def get_queue_size(self) -> int:
        """
        Get current queue size.

        Returns:
            Number of messages in queue
        """
        return self.message_queue.qsize()

    def format_message(self, entry: dict) -> str:
        """
        Format log entry for display.

        Args:
            entry: Log entry dict

        Returns:
            Formatted message string
        """
        return f"[{entry['timestamp']}] {entry['level']}: {entry['message']}"

    def get_formatted_messages(self, max_count: Optional[int] = None) -> list:
        """
        Get formatted messages from queue.

        Args:
            max_count: Maximum number of messages

        Returns:
            List of formatted message strings
        """
        messages = self.get_messages(max_count)
        return [self.format_message(entry) for entry in messages]


# Singleton instance for application-wide logging
_app_logger: Optional[GUILogger] = None
_logger_lock = threading.Lock()


def get_logger(
    name: str = "LinguaSplit",
    level: LogLevel = LogLevel.INFO,
    log_to_file: bool = False,
    log_file: Optional[str] = None
) -> GUILogger:
    """
    Get or create singleton logger instance.

    Args:
        name: Logger name
        level: Log level
        log_to_file: Whether to log to file
        log_file: Log file path

    Returns:
        GUILogger instance
    """
    global _app_logger

    with _logger_lock:
        if _app_logger is None:
            _app_logger = GUILogger(
                name=name,
                level=level,
                log_to_file=log_to_file,
                log_file=log_file
            )
        return _app_logger


def reset_logger():
    """Reset the singleton logger instance."""
    global _app_logger

    with _logger_lock:
        if _app_logger:
            _app_logger.clear()
        _app_logger = None
