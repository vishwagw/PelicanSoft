"""
Logging configuration for P8 Pro Drone Controller
Sets up structured logging for the application
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

def setup_logging(log_level=logging.INFO, log_to_file=True):
    """
    Setup application logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to write logs to file
    """
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "drone_controller.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
        
        # Separate error log
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
    
    # Set specific logger levels
    logging.getLogger('tkinter').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    logging.info("Logging system initialized")

class DroneLogger:
    """Custom logger for drone operations"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def flight_event(self, event: str, **kwargs):
        """Log flight-related events"""
        extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        message = f"FLIGHT: {event}"
        if extra_info:
            message += f" | {extra_info}"
        self.logger.info(message)
    
    def command_sent(self, command: str, response: Optional[str] = None):
        """Log sent commands and responses"""
        message = f"CMD: {command}"
        if response:
            message += f" -> {response}"
        self.logger.debug(message)
    
    def telemetry_update(self, data: dict):
        """Log telemetry updates"""
        important_fields = ['battery', 'altitude', 'speed']
        telemetry_summary = " | ".join([
            f"{field}={data.get(field, 'N/A')}" 
            for field in important_fields 
            if field in data
        ])
        if telemetry_summary:
            self.logger.debug(f"TELEMETRY: {telemetry_summary}")
    
    def safety_alert(self, alert: str, level: str = "WARNING"):
        """Log safety-related alerts"""
        log_method = getattr(self.logger, level.lower(), self.logger.warning)
        log_method(f"SAFETY: {alert}")
    
    def connection_event(self, event: str, details: Optional[str] = None):
        """Log connection-related events"""
        message = f"CONNECTION: {event}"
        if details:
            message += f" - {details}"
        self.logger.info(message)