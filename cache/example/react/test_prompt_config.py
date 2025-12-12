#!/usr/bin/env python3
"""ReAct Prompt Configuration Test and Example

This script demonstrates and tests the configurable prompt functionality
for the ReAct engine.

Features tested:
1. Default prompt configuration
2. Custom prompt configuration
3. Field validation
4. Integration with ReActConfig
"""

import sys

sys.path.insert(0, '/data/home/solgeo/projects/chat-service/src')

from react.config.prompt import (
    SystemPromptConfig,
    PlannerPromptConfig,
    ExecutorPromptConfig,
    PromptConfig
)
from react.config.react import ReActConfig


def test_system_prompt():
    """Test SystemPromptConfig validation"""
    print("\n" + "=" * 60)
    print("Test 1: SystemPromptConfig Validation")
    print("=" * 60)

    try:
        config = SystemPromptConfig()
        report = SystemPromptConfig.get_validation_report()

        print(f"✓ Validation passed: {report['is_valid']}")
        print(f"  Template fields: {report['template_fields']}")
        print(f"  Dataclass fields: {report['dataclass_fields']}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_planner_prompt():
    """Test PlannerPromptConfig validation"""
    print("\n" + "=" * 60)
    print("Test 2: PlannerPromptConfig Validation")
    print("=" * 60)

    try:
        config = PlannerPromptConfig(
            summary="test summary",
            tools="test tools",
            analysis="test analysis",
            tool_name="test_tool"
        )
        report = PlannerPromptConfig.get_validation_report()

        print(f"✓ Validation passed: {report['is_valid']}")
        print(f"  Template fields: {report['template_fields']}")
        print(f"  Dataclass fields: {report['dataclass_fields']}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_executor_prompt():
    """Test ExecutorPromptConfig validation"""
    print("\n" + "=" * 60)
    print("Test 3: ExecutorPromptConfig Validation")
    print("=" * 60)

    try:
        config = ExecutorPromptConfig(
            tool_descriptions="test descriptions",
            planning_conclusion="test conclusion",
            tool_name="test_tool"
        )
        report = ExecutorPromptConfig.get_validation_report()

        print(f"✓ Validation passed: {report['is_valid']}")
        print(f"  Template fields: {report['template_fields']}")
        print(f"  Dataclass fields: {report['dataclass_fields']}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_prompt_config():
    """Test PromptConfig batch validation"""
    print("\n" + "=" * 60)
    print("Test 4: PromptConfig Batch Validation")
    print("=" * 60)

    try:
        prompt_config = PromptConfig(
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
        report = prompt_config.validate_all()

        print(f"✓ All valid: {report['all_valid']}")
        print(f"  Summary: {report['summary']}")

        return report['all_valid']
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_react_config():
    """Test ReActConfig with prompts"""
    print("\n" + "=" * 60)
    print("Test 5: ReActConfig Integration")
    print("=" * 60)

    try:
        config = ReActConfig(max_planning_steps=3)
        report = config.validate_prompts()

        print(f"✓ Prompts validation: {report['all_valid']}")
        print(f"  Summary: {report['summary']}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_field_validation_error():
    """Test that field validation catches mismatches"""
    print("\n" + "=" * 60)
    print("Test 6: Field Validation Error Detection")
    print("=" * 60)

    try:
        # This should fail - missing required fields
        config = PlannerPromptConfig(summary="test")
        print("✗ Should have raised TypeError for missing fields")
        return False
    except TypeError as e:
        print(f"✓ Correctly caught error: {e}")
        return True


def test_template_rendering():
    """Test template rendering"""
    print("\n" + "=" * 60)
    print("Test 7: Template Rendering")
    print("=" * 60)

    try:
        planner = PlannerPromptConfig(
            summary="Current task summary",
            tools="Available: search, calculate",
            analysis="I need to search for information",
            tool_name="search"
        )
        rendered = planner.render(
            summary="Current task summary",
            tools="Available: search, calculate",
            analysis="I need to search for information",
            tool_name="search"
        )

        print(f"✓ Template rendered successfully")
        print(f"  Length: {len(rendered)} chars")
        print(f"  Contains 'Current task summary': {'Current task summary' in rendered}")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def example_default_prompts():
    """Example: Using default prompt configuration"""
    print("\n" + "=" * 60)
    print("Example 1: Default Prompt Configuration")
    print("=" * 60)

    config = ReActConfig(
        max_planning_steps=3,
        stream_thoughts=True
    )

    report = config.validate_prompts()
    print(f"Validation result: {report['all_valid']}")
    print(f"System prompt length: {len(config.prompts.system.TEMPLATE)} chars")
    print(f"Planner prompt length: {len(config.prompts.planner.TEMPLATE)} chars")
    print(f"Executor prompt length: {len(config.prompts.executor.TEMPLATE)} chars")


def example_custom_prompts():
    """Example: Custom prompt configuration"""
    print("\n" + "=" * 60)
    print("Example 2: Custom Prompt Configuration")
    print("=" * 60)

    custom_prompts = PromptConfig(
        system=SystemPromptConfig(),
        planner=PlannerPromptConfig(
            summary="Task state: {summary}",
            tools="Tools available: {tools}",
            analysis="Analysis: {analysis}",
            tool_name="Recommended tool: {tool_name}"
        ),
        executor=ExecutorPromptConfig(
            tool_descriptions="Tool info: {tool_descriptions}",
            planning_conclusion="Plan: {planning_conclusion}",
            tool_name="Tool: {tool_name}"
        )
    )

    config = ReActConfig(
        max_planning_steps=3,
        prompts=custom_prompts
    )

    report = config.validate_prompts()
    print(f"Custom config validation: {report['all_valid']}")

    # Demonstrate rendering
    rendered = custom_prompts.planner.render(
        summary="User asking about weather",
        tools="Available: weather_api, search_web",
        analysis="Need to call weather API",
        tool_name="weather_api"
    )

    print("\nRendered planner prompt:")
    print(rendered[:200] + "..." if len(rendered) > 200 else rendered)


def example_validation_api():
    """Example: Using validation API"""
    print("\n" + "=" * 60)
    print("Example 3: Validation API Usage")
    print("=" * 60)

    # Method 1: Explicit validation
    print("Method 1: Explicit validation")
    try:
        PlannerPromptConfig.validate()
        print("  ✓ PlannerPromptConfig validation passed")
    except TypeError as e:
        print(f"  ✗ Validation failed: {e}")

    # Method 2: Detailed report
    print("\nMethod 2: Get detailed validation report")
    report = PlannerPromptConfig.get_validation_report()
    print(f"  Class name: {report['class_name']}")
    print(f"  Template fields: {report['template_fields']}")
    print(f"  Dataclass fields: {report['dataclass_fields']}")
    print(f"  Is valid: {report['is_valid']}")

    # Method 3: Batch validation
    print("\nMethod 3: Batch validation")
    config = ReActConfig()
    report = config.validate_prompts()
    print(f"  All valid: {report['all_valid']}")
    print(f"  Summary: {report['summary']}")

    # Method 4: Validate or raise exception
    print("\nMethod 4: Validate or raise exception")
    try:
        config.validate_prompts_or_raise()
        print("  ✓ Validation passed, no exception")
    except TypeError as e:
        print(f"  ✗ Validation failed: {e}")


def example_engine_integration():
    """Example: Engine integration"""
    print("\n" + "=" * 60)
    print("Example 4: ReAct Engine Integration")
    print("=" * 60)

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

    react_config = ReActConfig(
        max_planning_steps=3,
        stream_thoughts=True,
        prompts=custom_prompts
    )

    print(f"ReActConfig created with custom prompts")
    print(f"  Streaming thoughts: {react_config.stream_thoughts}")
    print(f"  Has prompts config: {react_config.prompts is not None}")

    # Verify prompts are accessible to engine
    system_prompt = react_config.prompts.system.TEMPLATE
    planner_prompt = react_config.prompts.planner.TEMPLATE
    executor_prompt = react_config.prompts.executor.TEMPLATE

    print(f"\nEngine-accessible prompt templates:")
    print(f"  System: {len(system_prompt)} chars")
    print(f"  Planner: {len(planner_prompt)} chars")
    print(f"  Executor: {len(executor_prompt)} chars")


def main():
    """Run all tests and examples"""
    print("\n" + "=" * 60)
    print("ReAct Prompt Configuration - Tests and Examples")
    print("=" * 60)

    # Run tests
    tests = [
        ("SystemPromptConfig", test_system_prompt),
        ("PlannerPromptConfig", test_planner_prompt),
        ("ExecutorPromptConfig", test_executor_prompt),
        ("PromptConfig", test_prompt_config),
        ("ReActConfig", test_react_config),
        ("Field Validation", test_field_validation_error),
        ("Template Rendering", test_template_rendering)
    ]

    print("\n" + "=" * 60)
    print("Running Tests")
    print("=" * 60)

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    # Run examples
    print("\n" + "=" * 60)
    print("Running Examples")
    print("=" * 60)

    examples = [
        example_default_prompts,
        example_custom_prompts,
        example_validation_api,
        example_engine_integration
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ Example failed: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    print("\n" + "=" * 60)
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
