"""Result Validator

TODO: This module is currently NOT USED in the codebase.
      It provides ResultValidator class for validating execution results against expectations.

      Decision: Keep as extension for future use or remove if confirmed unnecessary.
      Related modules: core/validation/result.py
"""

import time
from typing import Any, Dict, List, Optional

from .result import (
    ValidationResult,
    QualityCheck,
    RelevanceCheck,
    CompletenessCheck
)


class ResultValidator:
    """Result Validator"""

    def __init__(self, llm_client=None, prompt_manager=None):
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager

    async def validate(
        self,
        result: Any,
        expected: Dict,
        context: Optional[Dict] = None
    ) -> ValidationResult:
        """Validate whether the result meets expectations"""

        start_time = time.time()
        context = context or {}

        validation_result = ValidationResult(
            passed=True,  # Default to pass
            quality_score=1.0
        )

        try:
            # Check 1: Data quality
            quality_check = await self.check_data_quality(result, expected)
            validation_result.quality_check = quality_check
            validation_result.checks.append(quality_check.to_dict())

            # Check 2: Completeness
            completeness_check = await self.check_completeness(result, expected)
            validation_result.completeness_check = completeness_check
            validation_result.checks.append(completeness_check.to_dict())

            # Check 3: Relevance
            relevance_check = await self.check_relevance(result, expected, context)
            validation_result.relevance_check = relevance_check
            validation_result.checks.append(relevance_check.to_dict())

            # Check 4: Freshness
            freshness_check = await self.check_freshness(result, expected)
            validation_result.checks.append(freshness_check.to_dict())

            # Comprehensive score
            validation_result.quality_score = self.calculate_quality_score([
                quality_check,
                completeness_check,
                relevance_check,
                freshness_check
            ])

            # Determine if passed
            threshold = expected.get("quality_threshold", 0.7)
            validation_result.passed = (
                quality_check.passed and
                completeness_check.passed and
                relevance_check.passed and
                validation_result.quality_score >= threshold
            )

            # Generate issues and suggestions
            if not validation_result.passed:
                self._generate_feedback(validation_result, [
                    quality_check,
                    completeness_check,
                    relevance_check
                ])

        except Exception as e:
            validation_result.passed = False
            validation_result.add_issue(f"Validation exception: {str(e)}")
            validation_result.quality_score = 0.0

        validation_result.validation_time = time.time() - start_time

        return validation_result

    async def check_data_quality(self, result: Any, expected: Dict) -> QualityCheck:
        """Check data quality"""
        issues = []
        score = 1.0

        # Check 1: Result is not empty
        if result is None:
            issues.append("Result is empty")
            score -= 0.5
        elif result == "":
            issues.append("Result is empty string")
            score -= 0.3

        # Check 2: Data type matches
        expected_type = expected.get("type")
        if expected_type and not self._check_type(result, expected_type):
            issues.append(f"Data type mismatch, expected: {expected_type}")
            score -= 0.3

        # Check 3: List length
        if isinstance(result, (list, dict)):
            expected_count = expected.get("count")
            if expected_count:
                actual_count = len(result) if isinstance(result, (list, dict)) else 0
                if self._evaluate_condition(actual_count, expected_count):
                    issues.append(f"Quantity does not meet requirements, expected: {expected_count}, actual: {actual_count}")
                    score -= 0.2

        # Check 4: Content quality (simple check)
        if isinstance(result, str):
            if len(result.strip()) < 10:
                issues.append("Content too short")
                score -= 0.2

        passed = score >= 0.6

        return QualityCheck(
            passed=passed,
            score=score,
            issue="; ".join(issues) if issues else None,
            details={"expected": expected, "actual_type": type(result).__name__}
        )

    async def check_completeness(self, result: Any, expected: Dict) -> CompletenessCheck:
        """Check completeness"""
        missing_fields = []
        score = 1.0

        # If expected is dict, check field completeness
        if isinstance(expected, dict) and "fields" in expected:
            expected_fields = expected["fields"]
            if isinstance(result, dict):
                for field in expected_fields:
                    if field not in result or result[field] is None:
                        missing_fields.append(field)

                if missing_fields:
                    score -= len(missing_fields) * 0.2

        # If expected is list, check minimum length
        if isinstance(expected, dict) and "min_items" in expected:
            min_items = expected["min_items"]
            if isinstance(result, list) and len(result) < min_items:
                missing_fields.append(f"At least {min_items} items required")
                score -= 0.3

        # If there are missing fields, consider it failed even if score is high
        passed = len(missing_fields) == 0 and score >= 0.7
        completeness_score = max(0.0, score)

        return CompletenessCheck(
            passed=passed,
            missing_fields=missing_fields,
            completeness_score=completeness_score
        )

    async def check_relevance(
        self,
        result: Any,
        expected: Dict,
        context: Dict
    ) -> RelevanceCheck:
        """Check relevance"""
        if not self.llm_client:
            # When no LLM client, use simple heuristic
            return self._simple_relevance_check(result, expected, context)

        try:
            # Use LLM to evaluate relevance
            prompt = await self._get_prompt(
                "relevance_check",
                result=str(result)[:500],
                expected=str(expected),
                context=str(context)[:200]
            )

            response = await self.llm_client.chat_completion([
                {"role": "system", "content": prompt}
            ])

            return self._parse_relevance_response(response.content)

        except Exception as e:
            # Fallback to simple check
            return self._simple_relevance_check(result, expected, context)

    async def check_freshness(self, result: Any, expected: Dict) -> QualityCheck:
        """Check freshness"""
        # Simple implementation: check timestamp or flag
        score = 1.0
        issues = []

        # If result contains time info, check if expired
        if isinstance(result, dict) and "timestamp" in result:
            import time as time_module
            result_time = result.get("timestamp")
            if isinstance(result_time, (int, float)):
                age = time_module.time() - result_time
                if age > 3600:  # 1 hour
                    issues.append("Result may be outdated")
                    score -= 0.2

        return QualityCheck(
            passed=score >= 0.7,
            score=score,
            issue="; ".join(issues) if issues else None
        )

    def calculate_quality_score(self, checks: List) -> float:
        """Calculate comprehensive quality score"""
        if not checks:
            return 0.0

        # Handle different types of check objects
        scores = []
        for check in checks:
            if hasattr(check, 'score'):
                scores.append(check.score)
            elif hasattr(check, 'completeness_score'):
                scores.append(check.completeness_score)
            elif hasattr(check, 'relevance_score'):
                scores.append(check.relevance_score)
            else:
                # Default score
                scores.append(1.0 if check.passed else 0.0)

        total_score = sum(scores)
        return total_score / len(checks)

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check data type"""
        type_map = {
            "string": str,
            "text": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "bool": bool
        }

        expected_python_type = type_map.get(expected_type.lower())
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True

    def _evaluate_condition(self, actual: Any, condition: str) -> bool:
        """Evaluate condition"""
        try:
            # Simple condition evaluation: >5, >=3, <10, etc.
            if condition.startswith(">"):
                threshold = float(condition[1:])
                return actual <= threshold  # Does not satisfy greater than condition

            elif condition.startswith(">="):
                threshold = float(condition[2:])
                return actual < threshold  # Does not satisfy greater than or equal to condition

            elif condition.startswith("<"):
                threshold = float(condition[1:])
                return actual >= threshold  # Does not satisfy less than condition

            elif condition.startswith("<="):
                threshold = float(condition[2:])
                return actual > threshold  # Does not satisfy less than or equal to condition

            elif condition.startswith("=="):
                expected = float(condition[2:])
                return actual != expected  # Does not satisfy equal to condition

            return False

        except (ValueError, TypeError):
            return False

    def _simple_relevance_check(
        self,
        result: Any,
        expected: Dict,
        context: Dict
    ) -> RelevanceCheck:
        """Simple relevance check (without LLM)"""
        score = 0.8  # Default score
        reason = "Based on heuristic rules"

        # Simple keyword matching
        if isinstance(result, str) and isinstance(context.get("query"), str):
            query_words = set(context["query"].lower().split())
            result_words = set(result.lower().split())
            overlap = len(query_words & result_words)

            if overlap > 0:
                score = min(0.9, 0.5 + overlap * 0.1)
            else:
                score = 0.5

        return RelevanceCheck(
            passed=score >= 0.6,
            score=score,
            reason=reason
        )

    def _generate_feedback(self, validation_result: ValidationResult, checks: List):
        """Generate issues and suggestions"""
        for check in checks:
            if isinstance(check, QualityCheck) and not check.passed:
                if check.issue:
                    validation_result.add_issue(f"Quality: {check.issue}")

            if isinstance(check, CompletenessCheck) and not check.passed:
                if check.missing_fields:
                    validation_result.add_issue(f"Missing fields: {', '.join(check.missing_fields)}")
                    validation_result.add_suggestion(f"Please provide missing fields: {', '.join(check.missing_fields)}")

            if isinstance(check, RelevanceCheck) and not check.passed:
                validation_result.add_issue(f"Relevance: {check.reason}")
                validation_result.add_suggestion("Please ensure result is related to query")

    async def _get_prompt(self, template_name: str, **kwargs) -> str:
        """Get prompt"""
        if not self.prompt_manager:
            return self._default_prompts.get(template_name, "")

        return await self.prompt_manager.get_template(template_name, **kwargs)

    def _parse_relevance_response(self, content: str) -> RelevanceCheck:
        """Parse relevance response"""
        try:
            import json

            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                raise ValueError("JSON not found")

            return RelevanceCheck(
                passed=data.get("score", 0.0) >= 0.6,
                score=float(data.get("score", 0.0)),
                reason=data.get("reason", "")
            )

        except Exception:
            return RelevanceCheck(
                passed=False,
                score=0.5,
                reason="Parsing failed"
            )

    _default_prompts = {
        "relevance_check": """
        You are a quality assessment expert.
        Objectively evaluate the relevance of the result to the query (0-1 score).

        Return JSON format:
        {
            "score": 0.0-1.0,
            "reason": "Assessment reason"
        }

        Scoring criteria:
        - 1.0: Fully relevant, accurately answered the query
        - 0.7-0.9: Mostly relevant, content has value
        - 0.5-0.7: Partially relevant, but not accurate enough
        - 0.0-0.5: Not relevant, did not answer the query
        """
    }
