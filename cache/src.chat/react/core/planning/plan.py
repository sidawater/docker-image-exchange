"""Execution Plan Definitions"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from .todo import TODO


@dataclass
class IntentAnalysis:
    """Intent analysis result"""
    intent_type: str  # "general" | "it_operation" | "knowledge_query"
    confidence: float  # 0.0-1.0
    complexity: str  # "simple" | "medium" | "complex"
    required_tools: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "intent_type": self.intent_type,
            "confidence": self.confidence,
            "complexity": self.complexity,
            "required_tools": self.required_tools,
            "metadata": self.metadata
        }


@dataclass
class ExecutionStrategy:
    """Execution strategy"""
    name: str
    max_steps: int = 10
    allow_retry: bool = True
    auto_validation: bool = True
    fallback_enabled: bool = True
    parameters: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "max_steps": self.max_steps,
            "allow_retry": self.allow_retry,
            "auto_validation": self.auto_validation,
            "fallback_enabled": self.fallback_enabled,
            "parameters": self.parameters
        }


@dataclass
class ExecutionPlan:
    """Execution plan"""
    todos: List[TODO]
    strategy: ExecutionStrategy
    intent: IntentAnalysis
    query: str
    context: Dict = field(default_factory=dict)
    version: str = "1.0"

    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "query": self.query,
            "intent": self.intent.to_dict(),
            "strategy": self.strategy.to_dict(),
            "todos": [todo.to_dict() for todo in self.todos],
            "context": self.context
        }

    def get_todo_by_id(self, todo_id: str) -> Optional[TODO]:
        """Get TODO by ID"""
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None

    def add_todo(self, todo: TODO, index: Optional[int] = None):
        """Add TODO"""
        if index is not None:
            self.todos.insert(index, todo)
        else:
            self.todos.append(todo)

    def remove_todo(self, todo_id: str) -> bool:
        """Delete TODO"""
        for i, todo in enumerate(self.todos):
            if todo.id == todo_id:
                del self.todos[i]
                return True
        return False

    def get_next_todo(self, current_todo_id: Optional[str] = None) -> Optional[TODO]:
        """Get next pending TODO"""
        if not self.todos:
            return None

        if current_todo_id is None:
            return self.todos[0]

        # Find current TODO index
        current_index = -1
        for i, todo in enumerate(self.todos):
            if todo.id == current_todo_id:
                current_index = i
                break

        if current_index == -1 or current_index + 1 >= len(self.todos):
            return None

        return self.todos[current_index + 1]


class PlanManager:
    """Plan manager"""

    def __init__(self):
        self.plans: Dict[str, ExecutionPlan] = {}

    def create_plan(self, plan_id: str, plan: ExecutionPlan):
        """Create plan"""
        self.plans[plan_id] = plan

    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get plan"""
        return self.plans.get(plan_id)

    def update_plan(self, plan_id: str, plan: ExecutionPlan):
        """Update plan"""
        if plan_id in self.plans:
            self.plans[plan_id] = plan

    def delete_plan(self, plan_id: str) -> bool:
        """Delete plan"""
        if plan_id in self.plans:
            del self.plans[plan_id]
            return True
        return False

    def list_plans(self) -> List[str]:
        """List all plan IDs"""
        return list(self.plans.keys())

    def clone_plan(self, source_id: str, target_id: str) -> Optional[ExecutionPlan]:
        """Clone plan"""
        source = self.get_plan(source_id)
        if source:
            import copy
            cloned = copy.deepcopy(source)
            self.create_plan(target_id, cloned)
            return cloned
        return None
