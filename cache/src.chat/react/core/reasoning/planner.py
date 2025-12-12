"""Module definition"""

from typing import List
from react.model.reasoning import Action
from react.model.execution import ReActState
from react.mcp.protocol.schema import Tool


class ActionPlanner:
    
    def __init__(self, llm_client) -> None:
        self.llm_client = llm_client

    async def plan_next_action(
        self,
        state: ReActState,
        tools: List['Tool']
    ) -> Action:
        """Module definition"""
        return Action(type="finish")
