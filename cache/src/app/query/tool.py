"""
Query rewrite tool functions
"""

from typing import List, Optional
from .content import REQUERY_SYSTEM_PROMPT
from .schema import QueryRewriteResult
from init.db import vllm_manager


async def rewrite_query(
    query: str,
    documents: List[str],
    history: Optional[List[dict]] = None,
) -> QueryRewriteResult:
    """
    Rewrite user question to make it more suitable for document retrieval

    :param query: User query question
    :param documents: List of recognized document names
    :return: Contains the rewritten question
    """
    history_record = ""
    if history:
        history_msg = []
        for message in history:
            if message.get('role') == "assistant":
                history_msg.append({"role": "it_assistant", "content": message.get('content')})
            else:
                history_msg.append(message)
        history_record = f"Conversation record between user and operations assistant:{str(history_msg)}"

    prompt_content = REQUERY_SYSTEM_PROMPT.format(
        history_record=history_record,
        document_list=documents
    )

    messages = [
        {"role": "system", "content": prompt_content},
        {"role": "user", "content": query},
    ]

    client = vllm_manager.get_client('text')
    rewritten_query = await client.chat_non_stream(
        messages=messages,
        model=None,
        temperature=0.1,
        use_chat_template_kwargs=True,
        enable_thinking=True
    )

    return QueryRewriteResult(rewritten_query=rewritten_query.strip())
