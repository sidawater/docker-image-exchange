"""Reflection Phase Implementation"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from react.core.validation.result import ValidationResult


@dataclass
class ReflectionResult:
    """Reflection Result"""
    success: bool
    error_type: str  # "none" | "temporary" | "parameter" | "irrecoverable"
    feedback: str
    improvements: List[str] = field(default_factory=list)
    param_modifications: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "error_type": self.error_type,
            "feedback": self.feedback,
            "improvements": self.improvements,
            "param_modifications": self.param_modifications,
            "metadata": self.metadata
        }


class ReflectionPhase:
    """Reflection Phase"""

    def __init__(self, llm_client=None, prompt_manager=None):
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager

    async def reflect(
        self,
        todo_description: str,
        result: Any,
        validation: ValidationResult,
        context: Optional[Dict] = None
    ) -> ReflectionResult:
        """Reflect on the execution process"""

        context = context or {}

        if not validation.passed:
            # Result did not pass validation, need in-depth analysis
            return await self._analyze_failure(todo_description, result, validation, context)
        else:
            # Result passed validation, analyze improvement space
            return await self._analyze_success(todo_description, result, validation, context)

    async def _analyze_failure(
        self,
        todo_description: str,
        result: Any,
        validation: ValidationResult,
        context: Dict
    ) -> ReflectionResult:
        """Analyze failure reasons"""

        if not self.llm_client:
            # When no LLM, use heuristic analysis
            return self._heuristic_failure_analysis(validation)

        try:
            prompt = await self._get_prompt(
                "failure_analysis",
                todo_description=todo_description,
                result=str(result)[:300],
                validation=validation.to_dict(),
                issues=validation.issues
            )

            response = await self.llm_client.chat_completion([
                {"role": "system", "content": prompt}
            ])

            return self._parse_reflection_response(response.content)

        except Exception as e:
            return ReflectionResult(
                success=False,
                error_type="parameter",
                feedback=f"Reflection analysis failed: {str(e)}"
            )

    async def _analyze_success(
        self,
        todo_description: str,
        result: Any,
        validation: ValidationResult,
        context: Dict
    ) -> ReflectionResult:
        """Analyze success experience"""

        if not self.llm_client:
            return ReflectionResult(
                success=True,
                error_type="none",
                feedback="Task completed successfully",
                improvements=["Good quality"]
            )

        try:
            prompt = await self._get_prompt(
                "success_analysis",
                todo_description=todo_description,
                result=str(result)[:300],
                validation=validation.to_dict()
            )

            response = await self.llm_client.chat_completion([
                {"role": "system", "content": prompt}
            ])

            reflection = self._parse_reflection_response(response.content)
            reflection.success = True
            reflection.error_type = "none"

            return reflection

        except Exception as e:
            return ReflectionResult(
                success=True,
                error_type="none",
                feedback="Task completed, but analysis failed"
            )

    def _heuristic_failure_analysis(self, validation: ValidationResult) -> ReflectionResult:
        """Heuristic failure analysis (without LLM)"""
        failed_checks = validation.get_failed_checks()

        if "quality" in failed_checks:
            return ReflectionResult(
                success=False,
                error_type="parameter",
                feedback="Data quality issue",
                improvements=["Check input parameters", "Validate data types"]
            )

        if "relevance" in failed_checks:
            return ReflectionResult(
                success=False,
                error_type="parameter",
                feedback="Result relevance insufficient",
                improvements=["Optimize query", "Adjust tool parameters"]
            )

        if "completeness" in failed_checks:
            return ReflectionResult(
                success=False,
                error_type="irrecoverable",
                feedback="Result incomplete",
                improvements=["Provide complete information"]
            )

        # Default analysis
        return ReflectionResult(
            success=False,
            error_type="parameter",
            feedback="Unknown error",
            improvements=["Check input", "Retry execution"]
        )

    async def _get_prompt(self, template_name: str, **kwargs) -> str:
        """Get prompt"""
        if not self.prompt_manager:
            return self._default_prompts.get(template_name, "")

        return await self.prompt_manager.get_template(template_name, **kwargs)

    def _parse_reflection_response(self, content: str) -> ReflectionResult:
        """Parse reflection response"""
        try:
            import json

            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                raise ValueError("JSON not found")

            return ReflectionResult(
                success=data.get("success", False),
                error_type=data.get("error_type", "parameter"),
                feedback=data.get("feedback", ""),
                improvements=data.get("improvements", []),
                param_modifications=data.get("param_modifications", {})
            )

        except Exception as e:
            return ReflectionResult(
                success=False,
                error_type="parameter",
                feedback=f"Parsing failed: {str(e)}"
            )

    _default_prompts = {
        "failure_analysis": """
        You are a reflection expert.
        Analyze the reasons for execution failure in depth and propose improvement suggestions.

        Analysis points:
        1. Identify error types (temporary/parameter/irrecoverable errors)
        2. Analyze root causes
        3. Propose specific improvement measures

        Return JSON format:
        {
            "success": false,
            "error_type": "temporary|parameter|irrecoverable",
            "feedback": "Analysis reason",
            "improvements": ["Improvement suggestion 1", "Improvement suggestion 2"],
            "param_modifications": {"parameter_name": "new_value"}
        }

        Error type description:
        - temporary: Temporary errors (network, load, etc.), can retry
        - parameter: Parameter or configuration errors, need to modify parameters
        - irrecoverable: Irrecoverable errors (missing data, etc.), need to skip
        """,

        "success_analysis": """
        You are a reflection expert.
        Analyze successful execution experience and extract reusable patterns.

        Analysis points:
        1. Summarize success factors
        2. Identify optimizable aspects
        3. Extract reusable experience

        Return JSON format:
        {
            "success": true,
            "error_type": "none",
            "feedback": "Summary",
            "improvements": ["Optimization suggestion 1", "Optimization suggestion 2"],
            "param_modifications": {}
        }
        """
    }
