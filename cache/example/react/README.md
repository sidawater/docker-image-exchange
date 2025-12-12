# ReAct Prompt Configuration Examples

This directory contains examples and tests for the configurable prompt functionality in the ReAct engine.

## Files

### 1. `demo_react.py`
Original ReAct engine demonstration script using default prompt configurations.

**Usage:**
```bash
python demo_react.py
```

### 2. `demo_custom_prompts.py`
Demonstrates how to use custom prompt configurations with the ReAct engine.

**Features:**
- Creating custom prompt configurations
- Validating prompt configurations
- Using custom prompts with ReActConfig
- Integration with the ReAct engine

**Usage:**
```bash
python demo_custom_prompts.py
```

### 3. `test_prompt_config.py`
Comprehensive test suite for prompt configuration functionality.

**Features:**
- Unit tests for all prompt configuration classes
- Integration tests with ReActConfig
- Field validation tests
- Template rendering tests
- Usage examples

**Usage:**
```bash
python test_prompt_config.py
```

**Test Coverage:**
- ✓ SystemPromptConfig validation
- ✓ PlannerPromptConfig validation
- ✓ ExecutorPromptConfig validation
- ✓ PromptConfig batch validation
- ✓ ReActConfig integration
- ✓ Field validation error detection
- ✓ Template rendering

## Quick Start

### Using Default Prompts

```python
from react.config.react import ReActConfig

# Use default prompts (automatically initialized)
config = ReActConfig(
    two_stage_mode=True,
    stream_thoughts=True
)
```

### Using Custom Prompts

```python
from react.config.prompt import (
    SystemPromptConfig,
    PlannerPromptConfig,
    ExecutorPromptConfig,
    PromptConfig
)
from react.config.react import ReActConfig

# Create custom prompts
custom_prompts = PromptConfig(
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

# Use custom prompts
config = ReActConfig(
    two_stage_mode=True,
    prompts=custom_prompts
)
```

### Validating Configuration

```python
# Validate all prompts
report = config.validate_prompts()
if report['all_valid']:
    print("Validation passed!")

# Or validate with exception
config.validate_prompts_or_raise()
```

## Prompt Classes

### SystemPromptConfig
System prompt for the ReAct reasoning agent.
- No variable fields
- Defines the role and output format

### PlannerPromptConfig
Planning phase prompt for two-stage mode.
- Fields: `summary`, `tools`, `analysis`, `tool_name`
- Used to analyze problems and decide next steps

### ExecutorPromptConfig
Execution phase prompt for two-stage mode.
- Fields: `tool_descriptions`, `planning_conclusion`, `tool_name`
- Used to generate precise tool call parameters

### PromptConfig
Container for all three prompt configurations.
- Provides batch validation methods
- Validates all prompts at once

## Validation API

### Individual Validation
```python
# Validate a single prompt class
PlannerPromptConfig.validate()

# Get detailed validation report
report = PlannerPromptConfig.get_validation_report()
print(f"Is valid: {report['is_valid']}")
print(f"Template fields: {report['template_fields']}")
print(f"Dataclass fields: {report['dataclass_fields']}")
```

### Batch Validation
```python
# Validate all prompts in a PromptConfig
report = prompt_config.validate_all()
print(f"All valid: {report['all_valid']}")
print(f"Summary: {report['summary']}")

# Validate with ReActConfig
report = config.validate_prompts()

# Validate or raise exception
config.validate_prompts_or_raise()
```

## Field Validation

The prompt configuration system automatically validates that:
1. Template fields (e.g., `{summary}`) match dataclass fields
2. Dataclass fields are all used in the template
3. Field names are exactly consistent

**Example of validation error:**
```python
# This will fail validation - missing 'tools' field
class BadPlanner(Prompt):
    TEMPLATE = "Summary: {summary}, Tools: {tools}"
    summary: str  # Missing 'tools' field!
```

## Notes

- All prompts are validated during initialization
- Default prompts are automatically created if none provided
- Field validation prevents template/field mismatches
- Custom prompts allow full control over reasoning behavior
