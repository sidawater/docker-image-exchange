#!/usr/bin/env python3
"""Custom Prompts ReAct Engine Demo

This script demonstrates how to use custom prompt configurations
with the ReAct engine.

Features demonstrated:
1. Creating custom prompt configurations
2. Using custom prompts with ReActConfig
3. Validation of prompt configurations
4. Integration with the ReAct engine
"""

import asyncio
import sys

sys.path.insert(0, '/data/home/solgeo/projects/chat-service/src')

from react.config.llm import LLMConfig
from react.config.mcp import MCPConfig
from react.config.react import ReActConfig
from react.config.prompt import (
    SystemPromptConfig,
    PlannerPromptConfig,
    ExecutorPromptConfig,
    PromptConfig
)
from react.manager import react_manager
from react.model.response import ResponseData, MessageType


base_type: str | None = None


def print_response(response: ResponseData):
    """Print streaming response data."""
    global base_type
    if response.message_type.value == base_type:
        print(response.data, end='')
    else:
        print(f'\n\nTYPE: [{response.message_type.value}]')
        print(response.data, end='')
    base_type = response.message_type.value


async def demo_custom_prompts():
    """Demonstrate custom prompt usage."""
    llm_config = LLMConfig(
        provider="openai",
        model="Text_LLM",
        api_key="dummy_key",
        base_url="http://10.1.0.4:8001/v1",
        temperature=0.1,
        max_tokens=2048
    )
    mcp_config = MCPConfig(servers=[
        MCPConfig.Server(
            name='document-mcp',
            type='sse',
            url='http://10.194.203.138/knowledge/mcp-service/mcp/',
        )
    ])

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

    # Validate custom prompts
    print("Validating custom prompts...")
    validation_report = custom_prompts.validate_all()
    print(f"Validation result: {validation_report['all_valid']}")
    print(f"Summary: {validation_report['summary']}")

    if not validation_report['all_valid']:
        print("Validation failed!")
        for name, result in validation_report['results'].items():
            if not result['is_valid']:
                print(f"  {name}: {result['errors']}")
        return

    await react_manager.initialize()
    query = "What to do if the server is very slow"

    # Use custom prompts in ReActConfig
    react_config = ReActConfig(
        stream_thoughts=True,
        prompts=custom_prompts  # Pass custom prompts here
    )

    print(f"\nReActConfig created with custom prompts")
    print(f"  Streaming thoughts: {react_config.stream_thoughts}")
    print(f"  Has prompts: {react_config.prompts is not None}")

    instance = await react_manager.create_instance(
        instance_id="demo_custom_prompts",
        llm_config=llm_config,
        mcp_config=mcp_config,
        react_config=react_config
    )

    print(f"\nExecuting query: {query}")
    print("=" * 60)

    result = await instance.agent.engine.execute(
        query,
        stream_callback=print_response
    )

    print(f"\n" + "=" * 60)
    print(f"Execution completed")
    print(f"  Mode: {result.mode}")
    print(f"  Execution time: {result.execution_time:.2f}s")
    print(f"  Tools used: {len(result.tools_used)}")

    await react_manager.close()


async def demo_default_vs_custom():
    """Demonstrate difference between default and custom prompts."""
    print("\n" + "=" * 60)
    print("Default vs Custom Prompts Comparison")
    print("=" * 60)

    # Default prompts
    default_config = ReActConfig()
    print("\nDefault Prompts:")
    print(f"  System prompt length: {len(default_config.prompts.system.TEMPLATE)} chars")
    print(f"  Planner prompt length: {len(default_config.prompts.planner.TEMPLATE)} chars")
    print(f"  Executor prompt length: {len(default_config.prompts.executor.TEMPLATE)} chars")

    # Custom prompts
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
    custom_config = ReActConfig(prompts=custom_prompts)

    print("\nCustom Prompts:")
    print(f"  System prompt length: {len(custom_config.prompts.system.TEMPLATE)} chars")
    print(f"  Planner prompt length: {len(custom_config.prompts.planner.TEMPLATE)} chars")
    print(f"  Executor prompt length: {len(custom_config.prompts.executor.TEMPLATE)} chars")

    print("\nBoth configurations use the same templates by default.")
    print("The difference is that custom prompts allow you to modify them.")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("Custom Prompts ReAct Engine Demo")
    print("=" * 60)

    try:
        # Compare default and custom
        await demo_default_vs_custom()

        # Run main demo
        await demo_custom_prompts()

        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
