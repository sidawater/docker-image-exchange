"""Reasoning-related Data Models"""

import time
from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class ReasoningStep:
    """Reasoning Step"""
    thought: 'Thought'
    action: Optional['Action'] = None
    observation: Optional['Observation'] = None


@dataclass
class Thought:
    """Thought"""
    content: str
    reasoning: str


@dataclass
class Action:
    """Action"""
    type: str
    tool_name: Optional[str] = None
    arguments: Dict = field(default_factory=dict)


@dataclass
class Observation:
    """Observation"""
    content: str
    tool_name: Optional[str] = None
    success: bool = True
    timestamp: str = field(default_factory=lambda: str(int(time.time())))
