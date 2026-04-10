"""
Logging configuration using Loguru.
"""

import sys
from loguru import logger
from app.core.config import settings


def configure_logging():
    """Configure loguru logger based on environment."""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # Add file handler for production
    if settings.environment == "production":
        logger.add(
            "logs/app.log",
            rotation="500 MB",
            retention="10 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )
    
    logger.info(f"Logging configured for {settings.environment} environment")
    return logger


# Initialize logger
log = configure_logging()
