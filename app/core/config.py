"""
This module contains class Config for collecting all info
"""
from functools import lru_cache
from pydantic_settings import BaseSettings

from .logging import get_logger


logger = get_logger(__name__)


class Config(BaseSettings):
    """
    Class config
    """
    VLLM_SERVER: str
    API_V1_PREFIX: str
    API_URL: str
    SYSTEM_PROMPT: str
    SQL_TEMPLATE: str

    class Config:
        """
        Here we should write env file name
        """
        env_file = ".env"


@lru_cache
def load_config() -> Config:
    """
    This function is used to load and return the config
    :return:
        Config
    """

    try:
        config = Config()
        logger.info("Config has been loaded")
        return config
    except Exception as e:
        logger.error("Error loading config: %s", e)
        return None
