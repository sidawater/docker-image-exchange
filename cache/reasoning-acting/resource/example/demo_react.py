"""Demo script for ReAct Engine with Memory

This script demonstrates how to initialize and use the ReAct Engine
with the new modular architecture (Planner, Executor, Memory).
"""
import sys

sys.path.insert(0, '/data/home/solgeo/projects/reasoning-acting/src')

import asyncio

from react.llm import llm_manager, VllmOpenaiConfig
from react.config.mcp import MCPConfig
from react.config.react import ReActConfig
from react.mcp.client.manager import MCPClientManager
from react.core.engine.engine import ReActEngine
from react.memory.memory import Memory
from react.model.response import ResponseData

LLM_ENDPOINT = "http://10.1.0.4:8001"
MCP_ENDPOINT = r"http://10.194.203.138/knowledge/mcp-service/mcp"
MESSAGE_TYPE: str = ''

async def create_llm_client():
    """Create and configure LLM client"""
    config = VllmOpenaiConfig(
        provider="vllm_openai",
        model="Text_LLM",
        api_key="dummy_key",
        base_url=LLM_ENDPOINT,
        temperature=0.1,
        max_tokens=2048,
        timeout=60.0,
        max_retries=3,
        stream=True,
        reasoning=False,
    )
    client = llm_manager.create("vllm_text", config)
    print(f"✓ LLM: {config.model} @ {config.base_url}")
    print(f"✓ Initialized")
    return client


def create_mcp_config() -> MCPConfig:
    """Create MCP configuration"""
    return MCPConfig(
        servers=[
            MCPConfig.Server(
                name="test_server",
                type="sse",
                url=MCP_ENDPOINT,
                timeout=30,
            )
        ],
        connection_timeout=30,
    )


async def create_mcp_manager():
    """Create and configure MCP manager"""
    config = create_mcp_config()
    manager = MCPClientManager(config)
    await manager.initialize()
    tools = manager.get_tools()
    print(f"✓ MCP: {MCP_ENDPOINT}, {len(tools)} tools")
    print(f"✓ Initialized")
    return manager


async def create_react_engine(llm_client, mcp_manager):
    """Create and configure ReAct Engine"""
    react_config = ReActConfig(max_execution_steps=10, stream_thoughts=True)
    memory = Memory(max_size=100)
    engine = ReActEngine(
        llm_client=llm_client,
        mcp_manager=mcp_manager,
        react_config=react_config,
        memory=memory
    )
    tools = mcp_manager.get_tools()
    engine.update_tools(tools)
    print(f"✓ ReAct: max_steps={react_config.max_execution_steps}, memory={memory.max_size}")
    print(f"✓ Initialized")
    return engine


async def stream_callback(response: ResponseData):
    """Handle streaming output"""
    global MESSAGE_TYPE
    if response.message_type.value != MESSAGE_TYPE:
        MESSAGE_TYPE = response.message_type.value
        print(f'\n\n{MESSAGE_TYPE}:\n')

    print(response.data, end='')


async def test_stream_with_tools_and_memory(engine: ReActEngine):
    """Test streaming with tools and memory"""
    query = "Calculate 5 + 3"
    print(f"\nQuery: {query}")

    result = await engine.execute(query, stream_callback=stream_callback)

    print(f"Answer: {result.answer[:100]}...")


async def main():
    """Main demo runner"""
    print("=" * 70)
    print("REACT ENGINE DEMO")
    print("=" * 70)

    llm_client = await create_llm_client()
    mcp_manager = await create_mcp_manager()
    engine = await create_react_engine(llm_client, mcp_manager)

    await test_stream_with_tools_and_memory(engine)

    await mcp_manager.close()
    await llm_client.close()


if __name__ == "__main__":
    asyncio.run(main())

