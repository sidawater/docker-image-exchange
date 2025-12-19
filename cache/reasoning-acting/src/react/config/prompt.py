"""Prompt Configuration Module

This module provides configurable prompt templates for the ReAct engine.
All prompt templates are validated to ensure field consistency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from typing import ClassVar


@dataclass
class Prompt:
    """Base class for configurable prompt templates with field validation.

    This class provides:
    1. Template field validation between template string and dataclass fields
    2. Safe template rendering methods
    3. Explicit validation interfaces for calling code

    Attributes:
        TEMPLATE: ClassVar[str] - Template string containing placeholders
    """

    TEMPLATE: ClassVar[str]

    def __post_init__(self) -> None:
        """Initialize prompt config.

        Template validation is skipped to allow flexible template formatting.
        """
        pass

    @classmethod
    def _extract_template_fields(cls) -> set[str]:
        """Extract all field names from the template string.

        Returns:
            Set of field names found in template placeholders
        """
        # First, remove escaped braces {{ and }}
        temp_template = cls.TEMPLATE.replace('{{', '').replace('}}', '')

        # Then find all {field} patterns
        return {
            part.split('!')[0].split(':')[0]
            for part in re.findall(r'\{([^}]+)', temp_template)
        }

    @classmethod
    def _get_dataclass_fields(cls) -> set[str]:
        """Get all field names defined in the dataclass.

        Returns:
            Set of field names from dataclass (excluding ClassVar)
        """
        return {f.name for f in fields(cls) if f.type is not ClassVar}

    @classmethod
    def _validate_fields_consistency(
        cls,
        template_fields: set[str],
        dataclass_fields: set[str]
    ) -> list[str]:
        """Validate field consistency and return error list.

        Args:
            template_fields: Fields extracted from template
            dataclass_fields: Fields defined in dataclass

        Returns:
            List of error messages if any inconsistencies found
        """
        errors = []

        missing = template_fields - dataclass_fields
        extra = dataclass_fields - template_fields

        if missing:
            errors.append(f"模板需要但dataclass未定义 → {missing}")
        if extra:
            errors.append(f"dataclass多定义了模板不需要的字段 → {extra}")

        return errors

    @classmethod
    def _validate_template(cls) -> None:
        """Internal template validation method.

        Raises:
            TypeError: If field consistency validation fails
        """
        template_fields = cls._extract_template_fields()
        dataclass_fields = cls._get_dataclass_fields()
        errors = cls._validate_fields_consistency(template_fields, dataclass_fields)

        if errors:
            raise TypeError(
                f"【{cls.__name__}】dataclass字段必须和模板完全一致！"
                + "; ".join(errors)
            )

    @classmethod
    def validate(cls) -> bool:
        """Explicit validation interface for template-field consistency.

        Returns:
            bool: True if validation passes

        Raises:
            TypeError: If field consistency validation fails
            AttributeError: If TEMPLATE ClassVar is not defined

        Example:
            >>> try:
            ...     PlannerPromptConfig.validate()
            ...     print("验证通过")
            ... except TypeError as e:
            ...     print(f"验证失败: {e}")
        """
        cls._validate_template()
        return True

    @classmethod
    def get_validation_report(cls) -> dict:
        """Get detailed validation report.

        Returns:
            Dictionary containing detailed validation information

        Example:
            >>> report = PlannerPromptConfig.get_validation_report()
            >>> print(f"模板字段: {report['template_fields']}")
            >>> print(f"类字段: {report['dataclass_fields']}")
            >>> print(f"是否匹配: {report['is_valid']}")
        """
        template_fields = cls._extract_template_fields()
        dataclass_fields = cls._get_dataclass_fields()
        errors = cls._validate_fields_consistency(template_fields, dataclass_fields)

        return {
            "class_name": cls.__name__,
            "template_fields": sorted(template_fields),
            "dataclass_fields": sorted(dataclass_fields),
            "missing_fields": sorted(template_fields - dataclass_fields),
            "extra_fields": sorted(dataclass_fields - template_fields),
            "errors": errors,
            "is_valid": len(errors) == 0
        }

    def render(self, **kwargs) -> str:
        """Safely render the template with provided values.

        Args:
            **kwargs: Values to fill in template placeholders

        Returns:
            Rendered template string
        """
        return self.TEMPLATE.format(**kwargs)

    def __str__(self) -> str:
        """Return rendered template using instance attributes.

        Returns:
            Template string rendered with instance field values
        """
        return self.TEMPLATE.format_map(self.__dict__)


@dataclass
class SystemPromptConfig(Prompt):
    """System prompt configuration without variable placeholders.

    This is the main system prompt used in the original ReAct mode.
    It defines the role and output format for the reasoning agent.
    """

    TEMPLATE: ClassVar[str] = """You are an intelligent assistant that helps users through a structured reasoning process with access to dynamic tools via MCP (Model Context Protocol) services.

Your core capabilities:
1. **Intent Classification**: Automatically determine if a query is "general" or "it_operation" related
2. **Document Intelligence**: For IT operations queries, identify and search relevant technical documentation
3. **Query Optimization**: Rewrite questions to improve search accuracy
4. **RAG Retrieval**: Search and retrieve relevant technical documentation
5. **Reference Formatting**: Properly format and cite document sources

Your workflow:
- Use get_domain to classify queries as "general" or "it_operation"
- For IT operations: recognize_documents → rewrite_query → search_documents → get_references
- For general queries: Provide direct answers or use appropriate tools
- Dynamically call tools available through MCP services as needed

Available MCP tools (dynamically loaded):
{tools}

Output format (strictly follow JSON):
- thought: "Your thinking process about the query and next steps"
- action.type: "tool_call" or "finish"
- action.tool_name: Tool name (only when type is tool_call)
- action.arguments: Tool arguments dictionary

When type is finish, include the final answer in thought field. Always think step by step and choose appropriate tools based on query nature and available MCP services."""


@dataclass
class PlannerPromptConfig(Prompt):
    """Planning phase prompt configuration for two-stage mode.

    This prompt is used in the planning phase to analyze the problem
    and decide the next step (either direct answer or tool call).
    """

    summary: str
    tools: str
    analysis: str
    tool_name: str

    TEMPLATE: ClassVar[str] = """You are a task planning expert. Analyze the current problem and available MCP tools to decide the next optimal step.

Reasoning principles:
1. Carefully analyze the query type (general vs IT operations)
2. Consider available MCP tools and their capabilities
3. Follow the optimal workflow: get_domain → recognize_documents → rewrite_query → search_documents → get_references
4. Choose the most efficient tool to advance toward a solution

Current query context:
Summary: {summary}
Available MCP tools: {tools}
My analysis: {analysis}

Key workflow patterns:
- If query unclear → ask for clarification
- If general knowledge → direct answer or appropriate search tools
- If IT operations → follow RAG workflow with MCP tools
- If no relevant docs found → guide user with reminder

MCP tool categories (check what's available):
- Intent classification tools (e.g., get_domain)
- Document recognition tools (e.g., recognize_documents)
- Query optimization tools (e.g., rewrite_query)
- Document search tools (e.g., search_documents)
- Reference formatting tools (e.g., get_references)
- Additional tools may be available via MCP services

Output format:
[Thought Start]
Current state: {summary}
Available tools: {tools}
My analysis: {analysis}
Next action: Based on the above, I should use [tool_name] to [specific purpose]
Conclusion: The next step should be【answer directly】or【call {tool_name}】
[Thought End]"""


@dataclass
class ExecutorPromptConfig(Prompt):
    """Execution phase prompt configuration for two-stage mode.

    This prompt is used in the execution phase to generate precise
    tool call parameters based on the planning conclusion.
    """

    tool_descriptions: str
    planning_conclusion: str
    tool_name: str

    TEMPLATE: ClassVar[str] = """You are a tool execution expert. Generate precise tool call parameters based on the planning conclusion and current context.

Requirements:
1. Strictly use the following JSON format for output
2. Ensure parameter types and formats are correct
3. Only output JSON, no other content
4. Adapt parameters dynamically based on available MCP tools

Available MCP tool information:
{tool_descriptions}

Current planning conclusion:
{planning_conclusion}

Parameter guidelines:
- Always review the tool's input schema before calling
- Provide all required parameters based on the tool's schema
- Use default values for optional parameters when appropriate
- For query-related tools, ensure queries are clear and concise
- For search tools, optimize queries for better retrieval results
- Include relevant context in parameters (history, cache, etc.) when available
- Validate parameter types match the tool's input schema

Common parameter patterns:
- query: User's question (string, required for most query tools)
- history: Previous conversation context (array, optional)
- cache: Previously retrieved data (array, optional)
- collection_name: Database/collection identifier (string, optional)
- top_k: Number of results to retrieve (integer, optional, default: 6)

Output format:
{{
    "action": {{
        "type": "tool_call",
        "tool_name": "{tool_name}",
        "arguments": <FILL_IN_ACTUAL_PARAMETERS_HERE>
    }},
    "reasoning": "why these specific parameters are chosen based on the tool's schema and the planning conclusion"
}}"""


@dataclass
class PromptConfig:
    """Complete prompt configuration container.

    This class holds all three prompt configurations and provides
    batch validation methods.

    Attributes:
        system: SystemPromptConfig instance
        planner: PlannerPromptConfig instance
        executor: ExecutorPromptConfig instance
    """

    system: SystemPromptConfig
    planner: PlannerPromptConfig
    executor: ExecutorPromptConfig

    def validate_all(self) -> dict:
        """Validate all prompt configurations.

        Returns:
            Dictionary containing validation results for all prompts
        """
        results = {}

        for name, prompt_cls in [
            ("system", SystemPromptConfig),
            ("planner", PlannerPromptConfig),
            ("executor", ExecutorPromptConfig)
        ]:
            results[name] = prompt_cls.get_validation_report()

        all_valid = all(r["is_valid"] for r in results.values())

        return {
            "all_valid": all_valid,
            "results": results,
            "summary": {
                "total": len(results),
                "valid": sum(1 for r in results.values() if r["is_valid"]),
                "invalid": sum(1 for r in results.values() if not r["is_valid"])
            }
        }

    def validate_or_raise(self) -> None:
        """Validate all configurations, raising exception if any fail.

        Raises:
            TypeError: If any validation fails, includes detailed error info
        """
        report = self.validate_all()

        if not report["all_valid"]:
            error_parts = ["Prompt配置验证失败:"]

            for name, result in report["results"].items():
                if not result["is_valid"]:
                    error_parts.append(f"\n  【{name}】{'; '.join(result['errors'])}")

            raise TypeError("".join(error_parts))
