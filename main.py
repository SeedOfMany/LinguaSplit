#!/usr/bin/env python3
"""
LinguaSplit - Multi-Language PDF Document Extractor

Main entry point for the application.
Handles initialization, logging setup, and GUI launch.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add linguasplit to path if running from source
sys.path.insert(0, str(Path(__file__).parent))

from linguasplit.utils.logger import GUILogger, LogLevel
from linguasplit.utils.config_manager import ConfigManager


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='LinguaSplit - Multi-Language PDF Document Extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Launch GUI
  %(prog)s --debug            # Launch with debug logging
  %(prog)s --config /path/to/config.json
        """
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--config',
        type=str,
        metavar='PATH',
        help='Path to configuration file'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='LinguaSplit 1.0.0'
    )

    parser.add_argument(
        '--reset-config',
        action='store_true',
        help='Reset configuration to defaults'
    )

    return parser.parse_args()


def setup_logging(debug: bool = False, config: ConfigManager = None):
    """
    Setup application logging.

    Args:
        debug: Enable debug logging
        config: Configuration manager

    Returns:
        GUILogger instance
    """
    # Determine log level
    if debug:
        level = LogLevel.DEBUG
    elif config:
        level_str = config.get('logging.level', 'INFO')
        level = getattr(LogLevel, level_str, LogLevel.INFO)
    else:
        level = LogLevel.INFO

    # Get logging settings from config
    log_to_file = config.get('logging.log_to_file', False) if config else False
    log_file = config.get('logging.log_file', 'linguasplit.log') if config else None

    # Create logger
    logger = GUILogger(
        name="LinguaSplit",
        level=level,
        log_to_file=log_to_file,
        log_file=log_file
    )

    return logger


def main():
    """Main application entry point."""
    # Parse arguments
    args = parse_arguments()

    # Load or create configuration
    try:
        config = ConfigManager(args.config)

        # Reset config if requested
        if args.reset_config:
            print("Resetting configuration to defaults...")
            config.reset(save=True)
            print(f"Configuration reset complete: {config.get_config_path()}")
            return 0

    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("Using default configuration.")
        config = ConfigManager()

    # Setup logging
    logger = setup_logging(debug=args.debug, config=config)
    logger.info("Starting LinguaSplit...")
    logger.info(f"Configuration loaded from: {config.get_config_path()}")

    if args.debug:
        logger.debug("Debug logging enabled")
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Platform: {sys.platform}")

    # Import GUI (delayed to allow logging setup first)
    try:
        import tkinter as tk
        from linguasplit.gui.main_window import LinguaSplitMainWindow

        # Try to use TkinterDnD for drag and drop support
        try:
            from tkinterdnd2 import TkinterDnD
            root = TkinterDnD.Tk()
            logger.info("Initializing GUI with drag & drop support...")
        except ImportError:
            root = tk.Tk()
            logger.info("Initializing GUI (tkinterdnd2 not available for drag & drop)...")

        # Set window properties from config
        window_size = config.get('gui.window_size', [1000, 700])
        root.geometry(f"{window_size[0]}x{window_size[1]}")

        # Create main application window
        app = LinguaSplitMainWindow(root)

        logger.info("LinguaSplit started successfully")

        # Start GUI event loop
        root.mainloop()

        logger.info("LinguaSplit closed")
        return 0

    except ImportError as e:
        print(f"Error: Failed to import required modules: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return 1

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {e}")
        print("See log file for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
