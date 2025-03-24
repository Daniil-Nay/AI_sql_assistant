"""
This module contains several routes to serve FastAPI server
"""

from fastapi import APIRouter

from app.core.logging import get_logger
from app.services.vllm_service import VLLMService
from pydantic import BaseModel

logger = get_logger(__name__)
router = APIRouter()
llm_service = VLLMService()


class QueryRequest(BaseModel):
    query: str


@router.get("/health")
async def health_check():
    """
    Healtheck
    should return status -- 'heatlhy'
    Args:
        None
    :return:
        {"status": "healthy", "model_loaded": true}

    """
    logger.info("Healtcheck has been called")
    try:
        res = await llm_service.health_check()
        logger.info("Healtcheck responsed", res)
        return res
    except Exception as e:
        logger.error("Healthcheck failed", str(e))


@router.post("/load-model")
async def load_model():
    """
    By this method we explicitly load the LLM model into memory.
    It is should be called before making any sql generation request
    """
    logger.info("Loading model attempt")
    try:
        res = await llm_service.load_model()
        logger.info("Model has been loaded", res)
        return res
    except Exception as e:
        logger.error("Error while loading model", str(e))


@router.post("/generate-sql")
async def generate_sql(request: QueryRequest):
    """
    Generates sql query from user prompt,
    :param request:  request from user
    :return: sql query
    """
    logger.info(f"SQL generation requested for {request.query}")
    try:
        res = await llm_service.generate_sql(request.query)
        logger.info("SQL generated successfully", res)
        return res
    except Exception as e:
        logger.error("Error while generating sql", str(e))
