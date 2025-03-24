"""
This module contains logging class
"""

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def get_logger(name: str) -> logging.Logger:
    """
    To get logger
    Args:
        logger name
    :returns: logger

    """
    return logging.getLogger(name)
