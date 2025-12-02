import logging
from typing import cast

from litellm import acompletion
from litellm.types.utils import ModelResponse
from temporalio import activity

logger = logging.getLogger(__name__)


USE_OLLAMA = False


@activity.defn
async def llm(prompt: str) -> str:
    """Query the LLM with a prompt.

    Returns:
        The LLM's response as a string
    """
    if USE_OLLAMA:
        logger.info("Querying LLM with prompt: %s", prompt)
        response = cast(
            ModelResponse,
            await acompletion(
                model="ollama_chat/qwen2:0.5b",  # Ultra-fast 0.5B parameter model
                messages=[
                    {"role": "user", "content": prompt},
                ],
                api_base="http://localhost:11434",
                timeout=10,  # Reduced timeout for faster model
                max_tokens=50,  # Limit output for speed
                temperature=0.1,  # Lower temperature for more deterministic output
            ),
        )
        logger.info("LLM response: %s", response)
        return response["choices"][0]["message"]["content"]
    else:
        return "fake-translation (ollama disabled)"
