"""
Text/LLM Factory for Structured Extraction

This module provides factory functions for creating language model instances
specifically for structured data extraction from OCR results.
"""
from langchain_openai import ChatOpenAI
from audit_agent.config.settings import get_config


def get_qwen3_text_llm():
    """
    Create a text model instance for structured extraction.

    The model is configured via environment variables:
    - LLM_BASE_URL: LLM API endpoint
    - LLM_API_KEY: LLM API key
    - LLM_MODEL_NAME: Model name (e.g., qwen3-14b-instruct)
    - LLM_TEMPERATURE: Temperature for generation (lower = more consistent)
    - LLM_MAX_TOKENS: Maximum output tokens

    Returns:
        ChatOpenAI instance configured for structured extraction
    """
    config = get_config()

    return ChatOpenAI(
        model=config.llm_model_name,
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
        max_tokens=config.llm_max_tokens,
        temperature=config.llm_temperature,
        timeout=60
    )
