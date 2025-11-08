#!/usr/bin/env python3
"""
P8 Pro Drone Controller V4
Main application entry point for controlling P8 Pro drone via WiFi
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import DroneControllerGUI
from utils.logger import setup_logging
from config.settings import load_config

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting P8 Pro Drone Controller V4")
    
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Create and run GUI application
        app = DroneControllerGUI(config)
        app.run()
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
    
    logger.info("P8 Pro Drone Controller V4 shutdown complete")

if __name__ == "__main__":
    main()