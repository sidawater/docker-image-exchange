"""
Intent recognition tool functions
"""

from .content import INTENT_SYSTEM_PROMPT
from .schema import IntentRecognitionResult
from init.db import vllm_manager


async def get_intent(query: str) -> IntentRecognitionResult:
    """
    Get user intent classification

    :param query: User query question
    :param model: Model name used
    :return: Contains intent classification result, format is {"intent": "general" | "it_operation"}
    """
    messages = [INTENT_SYSTEM_PROMPT, {"role": "user", "content": query}]

    client = vllm_manager.get_client('text')
    intent = await client.chat_non_stream(
        messages=messages,
        model=None,
        temperature=0.1
    )
    intent = intent.strip().lower()

    i = 0
    while not IntentRecognitionResult.is_valid_intent(intent) and i < 3:
        intent = await client.chat_non_stream(
            messages=messages,
            model=None,
            temperature=0.1
        )
        intent = intent.strip().lower()
        i += 1

    if IntentRecognitionResult.is_valid_intent(intent):
        return IntentRecognitionResult(intent=intent)

    return IntentRecognitionResult(intent="general")
