"""
Document recognition tool functions
"""

from typing import List, Optional
import ast
import re
from init.db import vllm_manager
from .prompts import (
    VALID_DOC_KEYS,
    DOC_KEY_ALIASES_MAPPING,
    DOC_RECOGNITION_SYSTEM_PROMPT
)
from .schema import DocumentRecognitionResult


def check_documents(document_list: List[str]) -> bool:
    """
    Check if all documents in the list are valid documents

    :param document_list: List of document names
    :return: Returns True if all documents are valid, otherwise False
    """
    large_set = set(VALID_DOC_KEYS)
    return all(item in large_set for item in document_list)


def clean_document_list(raw_data: str) -> List[str]:
    """
    Clean document list string

    :param raw_data: Raw document list string
    :return: Cleaned document list
    """
    cleaned_data = raw_data.strip()

    try:
        result = ast.literal_eval(cleaned_data)
        if isinstance(result, list):
            return result
    except (SyntaxError, ValueError):
        pass

    list_match = re.search(r'\[([^\[\]]*)\]', cleaned_data)
    if list_match:
        content = list_match.group(1).strip()

        if content:
            items = [item.strip().strip('"\'').strip() for item in content.split(',')]
            return items
        else:
            return []

    return []


def _build_history_record(history: Optional[List[dict]]) -> str:
    """
    Build history record description

    :param history: List of historical conversation records
    :return: Formatted history record description
    """
    if not history:
        return "Conversation record between user and operations assistant:[]"

    history_msg = []
    for message in history:
        if message.get('role') == "assistant":
            history_msg.append({"role": "it_assistant", "content": message.get('content')})
        else:
            history_msg.append(message)

    return f"Conversation record between user and operations assistant:{str(history_msg)}"


def _build_cache_desc(cache: Optional[List[str]]) -> str:
    """
    Build cache description

    :param cache: List of most recently used document names in system cache
    :return: Formatted cache description
    """
    if not cache or len(cache) == 0:
        return "Document names appearing in the most recent conversation in system cache:[]"

    if len(cache) == 1:
        return f"This is the document name appearing in the most recent conversation in system cache: {cache} ."

    return f"In the system cache, multiple documents were involved in the recent conversation: {cache} ."


def _build_prompt(
    query: str,
    history_record: str,
    cache_desc: str
) -> List[dict]:
    """
    Build model call message

    :param query: User query question
    :param history_record: History record description
    :param cache_desc: Cache description
    :return: List of messages
    """
    prompt_content = DOC_RECOGNITION_SYSTEM_PROMPT["content"].format(
        history_record=history_record,
        cache=cache_desc
    )

    prompt_content += f"\n\n### Document name alias mapping table:\n{DOC_KEY_ALIASES_MAPPING}\n"
    prompt_content += f"\n### Supported document list:\n{list(VALID_DOC_KEYS)}"

    return [
        {"role": "system", "content": prompt_content},
        {"role": "user", "content": query}
    ]


async def _call_model_with_retry(
    messages: List[dict],
    max_retries: int = 3
) -> str:
    """
    Model call with retry mechanism

    :param messages: List of messages
    :param model: Model name used
    :param endpoint: Model API endpoint
    :param max_retries: Maximum retry count
    :return: Raw data returned by the model
    """
    client = vllm_manager.client
    raw_data = await client.chat_non_stream(
        messages=messages,
        model=None,
        temperature=0.1,
        use_chat_template_kwargs=True,
        enable_thinking=True
    )

    i = 0

    while len(raw_data) > 80 and i < max_retries:
        raw_data = await client.chat_non_stream(
            messages=messages,
            model=None,
            temperature=0.1,
            use_chat_template_kwargs=True,
            enable_thinking=True
        )
        i += 1

    return raw_data


async def recognize_documents(
    query: str,
    history: Optional[List[dict]] = None,
    cache: Optional[List[str]] = None,
) -> DocumentRecognitionResult:
    """
    Recognize operations document names

    :param query: User query question
    :param history: List of historical conversation records
    :param cache: List of most recently used document names in system cache
    :param model: Model name used
    :param endpoint: Model API endpoint
    :return: Contains recognized document list, format is {"documents": List[str]}
    """
    history_record = _build_history_record(history)
    cache_desc = _build_cache_desc(cache)
    messages = _build_prompt(query, history_record, cache_desc)

    raw_data = await _call_model_with_retry(messages)

    document_list = clean_document_list(raw_data)

    client = vllm_manager.get_client('text')
    i = 0
    while document_list and not check_documents(document_list) and i < 3:
        raw_data = await client.chat_non_stream(
            messages=messages,
            model=None,
            temperature=0.1,
            use_chat_template_kwargs=True,
            enable_thinking=True
        )
        document_list = clean_document_list(raw_data)
        i += 1

    return DocumentRecognitionResult(documents=document_list if document_list else [])
