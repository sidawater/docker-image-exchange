"""ReAct Engine Configuration"""

from dataclasses import dataclass, field
from typing import Optional

from react.config.prompt import (
    PromptConfig,
    SystemPromptConfig,
    PlannerPromptConfig,
    ExecutorPromptConfig
)


def init_prompts():
    res = PromptConfig(
                system=SystemPromptConfig(),
                planner=PlannerPromptConfig(
                    summary="",
                    tools="",
                    analysis="",
                    tool_name=""
                ),
                executor=ExecutorPromptConfig(
                    tool_descriptions="",
                    planning_conclusion="",
                    tool_name=""
                )
            )
    return res


@dataclass
class ReActConfig:
    """ReAct Engine Configuration

    Attributes:
        stream_thoughts: Stream thinking process to callback
        max_planning_steps: Maximum planning steps in two-stage mode
        max_execution_steps: Maximum execution steps
        prompts: Optional prompt configuration, uses defaults if None
    """

    stream_thoughts: bool = True
    max_planning_steps: int = 3
    max_execution_steps: int = 10
    prompts: PromptConfig = field(default_factory=init_prompts)

    def validate_prompts(self) -> dict:
        """Validate current prompt configuration.

        Returns:
            Dictionary containing validation report
        """
        return self.prompts.validate_all()

    def validate_prompts_or_raise(self) -> None:
        """Validate prompts configuration, raising exception on failure.

        Raises:
            TypeError: If prompt validation fails with detailed error info
        """
        self.prompts.validate_or_raise()
