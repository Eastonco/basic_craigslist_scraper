"""
Craigslist Scraper Application
==============================

A Python application that monitors Craigslist for new listings and sends alerts
via SMS, email, or Discord when new items matching criteria are found.

Usage:
    python -m app --config ./config/config.json

Features:
    - Monitors multiple Craigslist URLs
    - Filters out unwanted listings based on keywords
    - Sends alerts via SMS (Twilio), Email (SMTP), or Discord webhooks
    - Stores listings in PostgreSQL database
    - Avoids duplicate notifications
    - Handles errors gracefully with retry logic
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from constants import DEFAULT_CONFIG_PATH
from core.scraper_app import CraigslistScraperApp
from exceptions import ConfigurationError, CraigslistScraperError
from models import Config, get_engine, get_db
from utils.logger import setup_logger


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Craigslist Scraper - Monitor Craigslist for new listings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m app --config ./config/config.json
    python -m app --config ./config/my_config.json --log-level DEBUG
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default=DEFAULT_CONFIG_PATH,
        help=f'Path to configuration file (default: {DEFAULT_CONFIG_PATH})'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set the logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        help='Optional file to write logs to'
    )
    
    return parser.parse_args()


def load_config(config_path: str) -> Config:
    """
    Load and validate configuration from JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Validated Config object
        
    Raises:
        ConfigurationError: If config loading or validation fails
    """
    try:
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Validate and create config object
        config = Config(**config_data)
        
        return config
        
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in config file {config_path}: {e}")
    except ValueError as e:
        raise ConfigurationError(f"Configuration validation error: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from {config_path}: {e}")


def setup_database(config: Config):
    """
    Set up database engine and model.
    
    Args:
        config: Application configuration
        
    Returns:
        Tuple of (engine, db_model_class)
        
    Raises:
        ConfigurationError: If database setup fails
    """
    try:
        # Create database engine
        engine = get_engine(
            user=config.db_user,
            password=config.db_password,
            host=getattr(config, 'db_host', 'localhost'),
            port=getattr(config, 'db_port', '5432'),
            database=getattr(config, 'db_name', 'craigslist'),
            echo=False
        )
        
        # Create database model based on config file name
        config_name = Path(sys.argv[0] if len(sys.argv) > 0 else 'default').stem
        db_model_class = get_db(config_name)
        
        return engine, db_model_class
        
    except Exception as e:
        raise ConfigurationError(f"Database setup failed: {e}")


def main() -> None:
    """
    Main entry point for the Craigslist scraper application.
    
    Raises:
        SystemExit: If a fatal error occurs
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logger(
        name="craigslist_scraper",
        level=args.log_level,
        log_file=args.log_file
    )
    
    try:
        logger.info("Starting Craigslist Scraper Application")
        logger.info(f"Configuration file: {args.config}")
        
        # Load configuration
        config = load_config(args.config)
        logger.info("Configuration loaded and validated successfully")
        
        # Set up database
        engine, db_model_class = setup_database(config)
        logger.info("Database setup completed")
        
        # Create and run the scraper application
        app = CraigslistScraperApp(
            config=config,
            engine=engine,
            db_model_class=db_model_class,
            logger=logger
        )
        
        # Run the application
        app.run()
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except CraigslistScraperError as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
