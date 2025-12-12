"""Module definition"""

from typing import Callable, Any
from react.model.execution import ReActState


class ReActLoop:
    
    def __init__(self, max_steps: int = 10) -> None:
        self.max_steps = max_steps

    async def run(
        self,
        initial_state: ReActState,
        step_fn: Callable[[ReActState], Any]
    ) -> ReActState:
        """Module definition"""
        state = initial_state
        while self.should_continue(state, state.step_count):
            state = await step_fn(state)
            state.step_count += 1
        return state

    def should_continue(self, state: ReActState, step_count: int) -> bool:
        """Module definition"""
        return step_count < state.max_steps
