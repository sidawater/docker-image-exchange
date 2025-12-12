"""Execution Context"""

from typing import List
from react.model.reasoning import ReasoningStep


class ExecutionContext:
    """Execution Context"""

    def __init__(self, query: str, max_steps: int = 10) -> None:
        self.query = query
        self.max_steps = max_steps
        self._steps: List[ReasoningStep] = []

    def add_step(self, step: ReasoningStep) -> None:
        """Add reasoning step"""
        self._steps.append(step)

    def get_context(self) -> str:
        """Get context"""
        return f"Query: {self.query}\nSteps: {len(self._steps)}"

    def get_steps(self) -> List[ReasoningStep]:
        """Get all steps"""
        return self._steps.copy()

    def get_step_count(self) -> int:
        """Get current step count"""
        return len(self._steps)
