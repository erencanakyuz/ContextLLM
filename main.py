#!/usr/bin/env python3
"""
ContextLLM - Main Entry Point
Professional file content aggregation tool for LLMs.
"""

import sys
import os
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_emergency_logging():
    """Setup emergency logging that works even if main logging fails"""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create emergency log file
    log_file = logs_dir / f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Setup basic logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("Emergency")

def main():
    """Main entry point for the ContextLLM application."""
    try:
        # Try importing and running the GUI first
        from gui.app import main as gui_main
        return gui_main()
    
    except ImportError as e:
        # Emergency logging setup for import errors
        emergency_logger = setup_emergency_logging()
        emergency_logger.info("ContextLLM Application Starting")
        emergency_logger.error(f"Failed to import GUI modules: {e}")

if __name__ == "__main__":
    main()