#!/usr/bin/env python3
"""
Logging Utility for ContextLLM
Provides centralized logging configuration and emergency logging capabilities.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional

class ContextLLMLogger:
    """Centralized logging configuration for ContextLLM"""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_dir = self._create_log_directory()
        self.logger = None
        self._setup_logger()
    
    def _create_log_directory(self) -> Path:
        """Create logs directory if it doesn't exist"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        return log_dir
    
    def _setup_logger(self):
        """Setup the main logger with file and console handlers"""
        # Create main logger
        self.logger = logging.getLogger("ContextLLM")
        self.logger.setLevel(self.log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler with rotation - Force flush for immediate writing
        log_file = self.log_dir / f"contextllm_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Force immediate writing to file
        class FlushingFileHandler(logging.handlers.RotatingFileHandler):
            def emit(self, record):
                super().emit(record)
                self.flush()  # Force immediate write
        
        # Replace with flushing handler
        file_handler = FlushingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler with flushing
        class FlushingStreamHandler(logging.StreamHandler):
            def emit(self, record):
                super().emit(record)
                self.flush()  # Force immediate write
        
        console_handler = FlushingStreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Store handlers for emergency flushing
        self.file_handler = file_handler
        self.console_handler = console_handler
        
        # Log startup information
        self.log_startup_info()
    
    def emergency_flush(self):
        """Force flush all log handlers immediately"""
        try:
            if hasattr(self, 'file_handler'):
                self.file_handler.flush()
            if hasattr(self, 'console_handler'):
                self.console_handler.flush()
            # Also flush the logger itself
            for handler in self.logger.handlers:
                handler.flush()
        except Exception:
            pass  # Don't let logging errors crash the app
    
    def log_startup_info(self):
        """Log application startup information"""
        import platform
        import sys
        
        self.logger.info("=" * 60)
        self.logger.info("ContextLLM - Application Started")
        self.logger.info("=" * 60)
        self.logger.info(f"Platform: {platform.system()} {platform.release()}")
        self.logger.info(f"Python: {sys.version.split()[0]}")
        self.logger.info(f"Log Level: {logging.getLevelName(self.log_level)}")
        self.logger.info(f"Log Directory: {self.log_dir.absolute()}")
        
        # Log PyQt6 information
        try:
            from PyQt6.QtCore import QT_VERSION_STR
            self.logger.info(f"PyQt6: {QT_VERSION_STR}")
        except ImportError:
            self.logger.warning("PyQt6 not found")
        
        # Try to log config info
        try:
            from config import APP_NAME, APP_VERSION
            self.logger.info(f"App Info: {APP_NAME} v{APP_VERSION}")
        except ImportError:
            self.logger.warning("Config not loaded yet")
        
        self.logger.info("-" * 60)
        self.emergency_flush()  # Force immediate write
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get a logger instance"""
        if name:
            return logging.getLogger(f"ContextLLM.{name}")
        return self.logger
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """Log performance metrics"""
        perf_logger = self.get_logger("Performance")
        message = f"{operation}: {duration:.3f}s"
        if details:
            message += f" | {details}"
        perf_logger.info(message)
    
    def log_user_action(self, action: str, details: str = ""):
        """Log user actions for analytics"""
        user_logger = self.get_logger("UserAction")
        message = f"User: {action}"
        if details:
            message += f" | {details}"
        user_logger.info(message)
    
    def log_error_with_context(self, error: Exception, context: str = ""):
        """Log error with full context and traceback"""
        error_logger = self.get_logger("Error")
        message = f"Error in {context}: {str(error)}"
        error_logger.exception(message)
    
    def log_file_operation(self, operation: str, file_path: str, success: bool = True, details: str = ""):
        """Log file operations"""
        file_logger = self.get_logger("FileOps")
        status = "SUCCESS" if success else "FAILED"
        message = f"{operation} | {status} | {file_path}"
        if details:
            message += f" | {details}"
        
        if success:
            file_logger.info(message)
        else:
            file_logger.error(message)
    
    def log_github_operation(self, operation: str, repo: str, success: bool = True, details: str = ""):
        """Log GitHub operations"""
        github_logger = self.get_logger("GitHub")
        status = "SUCCESS" if success else "FAILED"
        message = f"{operation} | {status} | {repo}"
        if details:
            message += f" | {details}"
        
        if success:
            github_logger.info(message)
        else:
            github_logger.error(message)
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Cleanup log files older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    removed_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to remove old log file {log_file}: {e}")
        
        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} old log files")

# Global logger instance
_logger_instance = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ContextLLMLogger()
    return _logger_instance.get_logger(name)

def setup_logging(log_level: str = "INFO") -> ContextLLMLogger:
    """Setup and return the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ContextLLMLogger(log_level)
    return _logger_instance

def log_performance(operation: str, duration: float, details: str = ""):
    """Convenience function for performance logging"""
    global _logger_instance
    if _logger_instance:
        _logger_instance.log_performance(operation, duration, details)

def log_user_action(action: str, details: str = ""):
    """Convenience function for user action logging"""
    global _logger_instance
    if _logger_instance:
        _logger_instance.log_user_action(action, details)

def log_error_with_context(error: Exception, context: str = ""):
    """Convenience function for error logging"""
    global _logger_instance
    if _logger_instance:
        _logger_instance.log_error_with_context(error, context)

def log_file_operation(operation: str, file_path: str, success: bool = True, details: str = ""):
    """Convenience function for file operation logging"""
    global _logger_instance
    if _logger_instance:
        _logger_instance.log_file_operation(operation, file_path, success, details)

def log_github_operation(operation: str, repo: str, success: bool = True, details: str = ""):
    """Convenience function for GitHub operation logging"""
    global _logger_instance
    if _logger_instance:
        _logger_instance.log_github_operation(operation, repo, success, details)

def emergency_flush():
    """Force flush all loggers immediately"""
    global _logger_instance
    if _logger_instance:
        _logger_instance.emergency_flush()

def log_critical_error(error: Exception, context: str = "", force_flush: bool = True):
    """Log critical error and force flush to ensure it's written"""
    global _logger_instance
    try:
        if _logger_instance:
            _logger_instance.log_error_with_context(error, context)
        else:
            # Fallback logging
            import traceback
            print(f"CRITICAL ERROR in {context}: {error}")
            traceback.print_exc()
        
        if force_flush:
            emergency_flush()
    except Exception:
        # Last resort - just print
        import traceback
        print(f"LOGGING FAILED - CRITICAL ERROR in {context}: {error}")
        traceback.print_exc()

# Performance timing decorator
def log_timing(operation_name: str = None):
    """Decorator to log function execution time"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance(name, duration, "Completed successfully")
                return result
            except Exception as e:
                duration = time.time() - start_time
                log_performance(name, duration, f"Failed: {str(e)}")
                raise
        return wrapper
    return decorator