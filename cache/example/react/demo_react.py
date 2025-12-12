#!/usr/bin/env python3
"""双阶段ReAct引擎演示脚本"""

import asyncio
import sys

sys.path.insert(0, '/data/home/solgeo/projects/chat-service/src')

from react.config.llm import LLMConfig
from react.config.mcp import MCPConfig
from react.config.react import ReActConfig
from react.manager import react_manager
from react.model.response import ResponseData, MessageType


base_type: str | None = None


def print_response(response: ResponseData):
    global base_type
    if response.message_type.value == base_type:
        print(response.data, end='')
    else:
        print(f'\n\nTYPE: [{response.message_type.value}]')
        print(response.data, end='')
    base_type = response.message_type.value


async def demo():
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

    await react_manager.initialize()
    query = "What to do if the server is very slow"
    react_config = ReActConfig(
        stream_thoughts=True
    )
    instance = await react_manager.create_instance(
        instance_id="demo2",
        llm_config=llm_config,
        mcp_config=mcp_config,
        react_config=react_config
    )
    result3 = await instance.agent.engine.execute(
        query,
        stream_callback=print_response
    )
    await react_manager.close()


if __name__ == '__main__':
    asyncio.run(demo())
