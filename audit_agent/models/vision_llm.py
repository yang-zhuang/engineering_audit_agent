"""
Vision LLM Factory for Region Detection

This module provides factory functions for creating vision model instances
used for detecting date, seal, and signature regions in engineering documents.
"""
from langchain_openai import ChatOpenAI
from audit_agent.config.settings import get_config


def get_vision_llm():
    """
    Create a vision model instance for region detection.

    The model is configured via environment variables:
    - VISION_MODEL_BASE_URL: Vision model API endpoint
    - VISION_MODEL_API_KEY: Vision model API key
    - VISION_MODEL_NAME: Model name (e.g., qwen3-vl-4b-instruct)

    Returns:
        ChatOpenAI instance configured for vision tasks
    """
    config = get_config()

    return ChatOpenAI(
        model=config.vision_model_name,
        api_key=config.vision_model_api_key,
        base_url=config.vision_model_base_url,
        max_tokens=8192,
        temperature=0,
        timeout=60
    )
