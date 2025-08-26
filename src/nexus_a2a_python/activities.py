import logging
from typing import cast

from litellm import acompletion
from litellm.types.utils import ModelResponse
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def llm(prompt: str) -> str:
    """Query the LLM with a prompt.

    Returns:
        The LLM's response as a string
    """
    logger.info("Querying LLM with prompt: %s", prompt)
    response = cast(
        ModelResponse,
        await acompletion(
            model="ollama_chat/gpt-oss",  # Use ollama_chat prefix for chat models
            messages=[
                {"role": "user", "content": prompt},
            ],
            api_base="http://localhost:11434",
            timeout=30,  # Increase timeout for model loading
        ),
    )
    logger.info("LLM response: %s", response)
    return response["choices"][0]["message"]["content"]
