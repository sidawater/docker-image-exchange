"""Module definition"""

import copy
import asyncio
from typing import Dict, Any, Optional, List

from react.core.planning.todo import TODO
from react.core.planning.plan import ExecutionPlan
from .reflector import ReflectionResult


class DynamicAdjustment:
    
    def __init__(self):
        self.adjustment_history: List[Dict] = []

    async def adjust_plan(
        self,
        current_plan: ExecutionPlan,
        failed_todo: TODO,
        reflection: ReflectionResult
    ) -> ExecutionPlan:
        """Module definition"""

        if reflection.error_type == "temporary":
            # ：
            return await self._handle_temporary_error(current_plan, failed_todo, reflection)

        elif reflection.error_type == "parameter":
            # ：
            return await self._handle_parameter_error(current_plan, failed_todo, reflection)

        elif reflection.error_type == "irrecoverable":
            # ：
            return await self._handle_irrecoverable_error(current_plan, failed_todo, reflection)

        else:
            # ：
            return await self._handle_unknown_error(current_plan, failed_todo, reflection)

    async def _handle_temporary_error(
        self,
        plan: ExecutionPlan,
        failed_todo: TODO,
        reflection: ReflectionResult
    ) -> ExecutionPlan:
        """："""

        if not failed_todo.can_retry():
            return await self._handle_irrecoverable_error(plan, failed_todo, reflection)

        # 
        failed_todo.increment_retry()

        # 
        self._record_adjustment(
            plan.query,
            failed_todo.id,
            "retry",
            {"retry_count": failed_todo.retry_count}
        )

        return plan

    async def _handle_parameter_error(
        self,
        plan: ExecutionPlan,
        failed_todo: TODO,
        reflection: ReflectionResult
    ) -> ExecutionPlan:
        """："""

        # TODO
        modified_todo = copy.deepcopy(failed_todo)

        # 
        for param, new_value in reflection.param_modifications.items():
            if param in modified_todo.params:
                old_value = modified_todo.params[param]
                modified_todo.params[param] = new_value

        # 
        modified_todo.retry_count = 0

        # TODO
        plan.remove_todo(failed_todo.id)
        plan.add_todo(modified_todo)

        # 
        self._record_adjustment(
            plan.query,
            failed_todo.id,
            "modify_params",
            {
                "param_modifications": reflection.param_modifications,
                "old_todo": failed_todo.to_dict(),
                "new_todo": modified_todo.to_dict()
            }
        )

        return plan

    async def _handle_irrecoverable_error(
        self,
        plan: ExecutionPlan,
        failed_todo: TODO,
        reflection: ReflectionResult
    ) -> ExecutionPlan:
        """：TODO"""

        # TODO
        plan.remove_todo(failed_todo.id)

        # 
        self._record_adjustment(
            plan.query,
            failed_todo.id,
            "skip",
            {
                "reason": reflection.feedback,
                "improvements": reflection.improvements
            }
        )

        return plan

    async def _handle_unknown_error(
        self,
        plan: ExecutionPlan,
        failed_todo: TODO,
        reflection: ReflectionResult
    ) -> ExecutionPlan:
        """："""

        # ：
        if failed_todo.can_retry():
            failed_todo.increment_retry()

            self._record_adjustment(
                plan.query,
                failed_todo.id,
                "default_retry",
                {"retry_count": failed_todo.retry_count}
            )

            return plan
        else:
            # ，
            return await self._handle_irrecoverable_error(plan, failed_todo, reflection)

    def _record_adjustment(
        self,
        query: str,
        todo_id: str,
        action: str,
        details: Dict
    ):
                import time

        self.adjustment_history.append({
            "timestamp": time.time(),
            "query": query,
            "todo_id": todo_id,
            "action": action,
            "details": details
        })

        # 100
        if len(self.adjustment_history) > 100:
            self.adjustment_history = self.adjustment_history[-100:]

    def get_adjustment_history(self, query: Optional[str] = None) -> List[Dict]:
        """Module definition"""
        if query:
            return [record for record in self.adjustment_history if record["query"] == query]

        return self.adjustment_history

    def get_todo_adjustment_count(self, todo_id: str) -> int:
        """TODO"""
        count = 0
        for record in self.adjustment_history:
            if record["todo_id"] == todo_id:
                count += 1
        return count


class RetryStrategy:
    
    @staticmethod
    async def exponential_backoff(attempt: int, base_delay: float = 1.0) -> float:
        """Module definition"""
        delay = base_delay * (2 ** attempt)
        # ，
        import random
        jitter = random.uniform(0, 0.1 * delay)
        return delay + jitter

    @staticmethod
    async def linear_backoff(attempt: int, base_delay: float = 1.0) -> float:
        """Module definition"""
        return base_delay * (attempt + 1)

    @staticmethod
    async def fixed_delay(delay: float) -> float:
        """Module definition"""
        return delay
