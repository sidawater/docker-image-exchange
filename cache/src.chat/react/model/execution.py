"""Execution-related Data Models"""

from dataclasses import dataclass
from typing import List
from .reasoning import ReasoningStep
from .tool import ToolCall
from react.memory.observation import Observation

@dataclass
class ExecutionResult:
    """Execution Result"""
    answer: str
    reasoning_steps: List['ReasoningStep']
    tools_used: List['ToolCall']
    execution_time: float
    mode: str = "original"


@dataclass
class ExecutionState:
    """Execution State"""
    current_step: int
    context: str
    observations: List['Observation']


@dataclass
class ReActState:
    """ReAct Loop State"""
    query: str
    step_count: int
    max_steps: int
    context: str
    observations: List['Observation']
    reasoning_steps: List['ReasoningStep']
