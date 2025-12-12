"""Answer Synthesizer"""

from typing import List
from react.model.reasoning import Observation


class AnswerSynthesizer:
    """Answer synthesizer"""

    def __init__(self, llm_client) -> None:
        self.llm_client = llm_client

    async def synthesize(
        self,
        query: str,
        observations: List[Observation],
        context: str
    ) -> str:
        """Synthesize answer"""
        return f"Synthesized answer for: {query}"
