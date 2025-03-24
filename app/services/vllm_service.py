"""
This module provides a wrapper around vLLM's API endpoints for model loading,
query generation and health checking.
"""

import aiohttp
from fastapi import HTTPException
from app.core.logging import get_logger
from app.core.config import load_config
from app.core.prompts import Prompts

logger = get_logger(__name__)


class VLLMService:
    """
    A service class for managing interactions with vllm
    attributes:
        vllm_url (str): the vllm service url
        _is_loaded (bool): is model loaded or no
        _is_loading (bool): is model being loaded now or no
        _load_error (str): stores errors while loadinng
        _prompts (Prompts): prompts generator instance
    """

    def __init__(self, vllm_url: str = None):
        """
        Initializes vllm service.

        Args:
            vllm_url (str): The url
        """
        config = load_config()
        self.vllm_url = vllm_url or config.VLLM_SERVER
        self._is_loaded = False
        self._is_loading = False
        self._load_error = None
        self._prompts = Prompts()
        logger.info("vllmservice initialized with url:%s", self.vllm_url)

    async def load_model(self) -> dict:
        """
        This method loads the model through vllm api.

        Args:
            None
        Returns:
            dict: a model status

        Raises:
            HTTPException: if there is an error while loading the llm
        """
        if self._is_loaded:
            return {"status": "Model already loaded"}

        if self._is_loading:
            return {"status": "Model is currently loading"}

        self._is_loading = True

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.vllm_url}/v1/models") as response:
                    if response.status == 200:
                        self._is_loaded = True
                        return {"status": "Model loaded successfully"}
                    else:
                        raise Exception(
                            "vLLM health check failed with status: %s",
                            str(response.status),
                        )

        except Exception as e:
            error_msg = f"Failed to connect to vLLM: {str(e)}"
            logger.error(error_msg)
            self._load_error = error_msg
            raise HTTPException(status_code=500, detail=error_msg)
        finally:
            self._is_loading = False

    async def generate_sql(self, query: str) -> dict:
        """
        This method generates an sql query based on input
        Generate an SQL query based on the natural language input.

        Arguments:
            query (str): the sql query
        Returns:
            dict:
                - sql: One-line version suitable for execution
                - sql_formatted: Multi-line formatted version for display

        Raises:
            HTTPException: If there is an error in generation or the model isn't loaded
        """
        if not self._is_loaded:
            return {"status": "Model not loaded. Please call /load-model first"}

        try:
            prompt = self._prompts.create_sql_prompt(query)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vllm_url}/v1/completions",
                    json={
                        "model": "/model",
                        "prompt": prompt,
                        "max_tokens": 200,
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "stop": ["###", "Comment:", "\n\n"],
                    },
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"vLLM error: {error_text}")
                        raise Exception(
                            "vLLM generation failed with status %s",
                            str(response.status),
                        )

                    result = await response.json()
                    logger.info("raw response: %s", str(result))

                    if not result.get("choices"):
                        raise Exception("no choices")

                    sql = result["choices"][0]["text"].strip()
                    logger.info("initial SQL: %s", str(sql))

                    sql = sql.replace("\\begin{code}", "").replace("\\end{code}", "")
                    sql = sql.replace("```sql", "").replace("```", "")
                    sql = sql.split("\n\n")[0].split("Comment:")[0].strip()

                    logger.info("cleaned SQL: %s", str(sql))

                    if not sql or "..." in sql:
                        raise Exception("generated SQL query is incomplete")

                    if not sql.endswith(";"):
                        sql = sql + ";"

                    sql_oneline = sql.replace("\n", " ").replace("  ", " ")

                    return {"sql": sql_oneline, "sql_formatted": sql}

        except Exception as e:
            logger.error("error generating SQL: %s", str(e))
            raise HTTPException(status_code=500)

    async def health_check(self) -> dict:
        """
        Check the health status of the service.

        Returns:
            dict: Contains the current health status and model loading state
        """
        return {"status": "healthy", "model_loaded": self._is_loaded}
