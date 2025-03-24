"""
This module contains Prompts class providing a specific structure
"""

from app.core.config import load_config
from app.core.logging import get_logger

logger = get_logger(__name__)


class Prompts:
    """
    Class for sql prompt generation for llm.
    """

    def __init__(self):
        """
        Here we load confgirutaion from env file.
        """
        self.config = load_config()
        logger.info("Prompts initialized with config")

    def create_sql_prompt(self, context: str, schema: str = None) -> str:
        """
        Generating an sql prompt based on context and schema
        Args:
            :param context: input context to generate sql query
            :param schema: if available then we use database schema
        :return:
            str: formatted sql prompt
        """
        try:
            logger.info("Creating SQL prompt with context: %s", str(context))

            if schema:
                logger.info("Using schema: %s", schema)

            system_prompt = self.config.SYSTEM_PROMPT

            if schema:
                system_prompt += f"\nDatabase schema:\n{schema}"

            prompt = self.config.SQL_TEMPLATE.format(
                system_prompt=system_prompt, context=context
            )

            logger.info("Prompt generated succesfully")
            return prompt
        except Exception as e:
            logger.error("Error while creating sql prompt: %s", str(e))
