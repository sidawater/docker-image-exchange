"""Validation Result Definitions

TODO: This module is currently NOT USED in the codebase.
      It provides ValidationResult, QualityCheck, RelevanceCheck, and CompletenessCheck
      classes for validation results.

      Decision: Keep as extension for future use or remove if confirmed unnecessary.
      Related modules: core/validation/validator.py, core/reflection/reflector.py
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class QualityCheck:
    """Quality check result"""
    passed: bool
    score: float = 0.0
    issue: Optional[str] = None
    details: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "issue": self.issue,
            "details": self.details
        }


@dataclass
class RelevanceCheck:
    """Relevance check result"""
    passed: bool
    score: float = 0.0
    reason: Optional[str] = None
    relevance_details: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "reason": self.reason,
            "relevance_details": self.relevance_details
        }


@dataclass
class CompletenessCheck:
    """Completeness check result"""
    passed: bool
    missing_fields: List[str] = field(default_factory=list)
    completeness_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "missing_fields": self.missing_fields,
            "completeness_score": self.completeness_score
        }


@dataclass
class ValidationResult:
    """Validation result"""
    passed: bool
    quality_score: float = 0.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    checks: List[Dict] = field(default_factory=list)

    # Check result details
    quality_check: Optional[QualityCheck] = None
    relevance_check: Optional[RelevanceCheck] = None
    completeness_check: Optional[CompletenessCheck] = None

    # Metadata
    validation_time: float = 0.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "quality_score": self.quality_score,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "checks": self.checks,
            "quality_check": self.quality_check.to_dict() if self.quality_check else None,
            "relevance_check": self.relevance_check.to_dict() if self.relevance_check else None,
            "completeness_check": self.completeness_check.to_dict() if self.completeness_check else None,
            "validation_time": self.validation_time,
            "metadata": self.metadata
        }

    def add_issue(self, issue: str):
        """Add issue"""
        self.issues.append(issue)

    def add_suggestion(self, suggestion: str):
        """Add suggestion"""
        self.suggestions.append(suggestion)

    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """Is acceptable"""
        return self.quality_score >= threshold

    def get_failed_checks(self) -> List[str]:
        """Get failed checks"""
        failed = []
        if self.quality_check and not self.quality_check.passed:
            failed.append("quality")
        if self.relevance_check and not self.relevance_check.passed:
            failed.append("relevance")
        if self.completeness_check and not self.completeness_check.passed:
            failed.append("completeness")
        return failed
