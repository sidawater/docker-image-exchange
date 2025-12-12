"""
Search tool functions

Provides operations documentation search and formatting functionality
"""
import traceback
import logging
from typing import List, Dict, Any
from init.vector import get_embedding_manager, get_qdrant_manager

logger = logging.getLogger(__name__)


async def search_documents(
    query: str,
    top_k: int = 6
) -> Dict[str, Any]:
    """
    Search operations documentation content

    :param query: Rewritten question
    :param top_k: Number of similar documents to return
    :return: Contains search results, format is {
        "status": "success" | "failed",
        "results": List[Dict],
        "error": str (optional)
    """
    try:
        embedding_manager = get_embedding_manager()
        qdrant_manager = get_qdrant_manager()

        embedding = await embedding_manager.client.get_embedding(query)
        search_results = await qdrant_manager.client.search(
            collection_name="documents",
            query_vector=embedding,
            limit=top_k,
        )

        results = []
        for record in search_results:
            payload = record.payload or {}
            result_item = {
                "id": record.id,
                "score": getattr(record, 'score', 0.0),
                "text": payload.get("text", ""),
                "title": payload.get("title", ""),
                "url": payload.get("url", ""),
                "anchor_id": payload.get("anchor_id", ""),
                "doc_key": payload.get("doc_key", ""),
            }
            results.append(result_item)

        return {
            "status": "success",
            "results": results
        }

    except Exception as e:
        logger.error(f'error: {e}, {traceback.format_exc()}')
        return {
            "status": "failed",
            "results": [],
            "error": f"Document search failed"
        }


def get_references(
    search_results: List[Dict[str, Any]],
    query: str
) -> List[Dict[str, Any]]:
    """
    Format reference documents

    :param search_results: List of search results
    :param query: Original query question
    :return: Formatted list of reference documents
    """
    formatted = []

    for idx, item in enumerate(search_results):
        try:
            score = float(item.get("score", 0.0))
        except (ValueError, TypeError):
            score = 0.0

        text = item.get("text", "")
        preview = text[:200] + "..." if len(text) > 200 else text

        ref_item = {
            "id": f"ref_{idx}",
            "title": item.get("title", "Untitled"),
            "url": item.get("url", ""),
            "anchor_id": item.get("anchor_id", ""),
            "doc_key": item.get("doc_key", ""),
            "score": round(score, 3),
            "preview": preview,
            "source_query": query,
        }
        formatted.append(ref_item)

    return formatted
