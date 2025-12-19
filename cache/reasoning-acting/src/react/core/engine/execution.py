"""Execution Phase 模块

实现 ReAct 引擎的 Execution Phase，负责执行工具调用和生成最终回答。
"""

import json
from typing import Callable, Dict, List, Optional

from react.config.react import ReActConfig
from react.llm.client import LLMClient
from react.model.reasoning import Observation
from react.model.response import MessageType, ResponseData
from react.model.tool import ToolCall


class Executor:
    """执行器

    负责执行工具调用和生成最终回答。
    """

    def __init__(
        self,
        llm_client: LLMClient,
        config: ReActConfig,
        tools: List,
        mcp_manager
    ) -> None:
        """初始化执行器

        :param llm_client: LLM 客户端
        :param config: ReAct 配置
        :param tools: 可用工具列表
        :param mcp_manager: MCP 管理器
        """
        self.llm_client = llm_client
        self.config = config
        self.tools = tools
        self.mcp_manager = mcp_manager

    async def execute_tool_call(
        self,
        tool_name: str,
        arguments: Dict,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> Observation:
        """执行工具调用

        :param tool_name: 工具名称
        :param arguments: 工具参数
        :param stream_callback: 流式回调
        :return: 观察结果
        """
        if not self.mcp_manager:
            return Observation(
                content="MCP manager not available",
                tool_name=tool_name,
                success=False
            )

        try:
            result = await self.mcp_manager.call_tool(tool_name, arguments)

            if result.is_error:
                return Observation(
                    content=f"Tool execution error: {result.error_message}",
                    tool_name=tool_name,
                    success=False
                )

            content_text = ""
            for item in result.content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        content_text += item.get("text", "")
                else:
                    content_text += str(item)

            return Observation(
                content=content_text or "Tool execution successful",
                tool_name=tool_name,
                success=True
            )

        except Exception as e:
            return Observation(
                content=f"Tool execution exception: {str(e)}",
                tool_name=tool_name,
                success=False
            )

    async def generate_tool_call(
        self,
        planning_result: Dict,
        query: str,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> Dict:
        """生成工具调用

        :param planning_result: 规划结果
        :param query: 用户查询
        :param stream_callback: 流式回调
        :return: 工具调用数据
        """
        messages = self._build_execution_messages(planning_result, query)

        tool_name = planning_result.get('tool_name', 'unknown')
        if stream_callback:
            await self._stream_output(
                stream_callback,
                MessageType.STATUS,
                {"status": "preparing_tool_call", "tool_name": tool_name}
            )

        response = await self._execute_llm_call(
            messages=messages,
            stream=False,
            stream_callback=stream_callback
        )

        return self._parse_execution_result(response)

    async def generate_answer(
        self,
        query: str,
        history: List[Dict],
        planning_result: Dict,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> str:
        """生成最终回答

        :param query: 用户查询
        :param history: 推理历史
        :param planning_result: 规划结果
        :param stream_callback: 流式回调
        :return: 回答内容
        """
        context_parts = []
        for step in history:
            if step.get("action") and step["action"].get("type") == "tool_call":
                context_parts.append(f"Called {step['action']['tool_name']}")
                if step.get("observation"):
                    context_parts.append(f"Result: {step['observation']['content']}")

        context = "\n".join(context_parts) if context_parts else "No tools were called"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Based on the reasoning process "
                    "and available information, provide a clear and helpful answer "
                    "to the user's question. Be concise but comprehensive."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Question: {query}\n\n"
                    f"Reasoning context:\n{context}\n\n"
                    f"Analysis: {planning_result.get('thought', '')}\n\n"
                    "Please provide the final answer:"
                )
            }
        ]

        answer = await self._execute_llm_call(
            messages=messages,
            stream=True,
            stream_callback=stream_callback,
            message_type=MessageType.CONTENT,
            enable_thinking=True
        )

        return answer

    def _build_execution_messages(
        self,
        planning_result: Dict,
        query: str
    ) -> List[Dict]:
        """构建执行消息

        :param planning_result: 规划结果
        :param query: 用户查询
        :return: 消息列表
        """
        tools_desc = self._build_tools_description()
        tool_name = planning_result.get('tool_name', 'unknown')

        return [
            {
                "role": "system",
                "content": self.config.prompts.executor.TEMPLATE.format(
                    tool_descriptions=tools_desc,
                    planning_conclusion=planning_result.get('raw_conclusion', ''),
                    tool_name=tool_name
                )
            },
            {
                "role": "user",
                "content": f"User query: {query}\n\nPlease generate JSON format tool call parameters."
            }
        ]

    def _build_tools_description(self) -> str:
        """构建工具描述

        :return: 工具描述文本
        """
        if not self.tools:
            return "No available tools"

        descriptions = []
        for tool in self.tools:
            desc = f"- {tool.name}: {tool.description}"
            if hasattr(tool, 'input_schema') and tool.input_schema:
                params = tool.input_schema.get("properties", {})
                if params:
                    param_str = ", ".join(params.keys())
                    desc += f" (parameters: {param_str})"
            descriptions.append(desc)

        return "\n".join(descriptions)

    async def _execute_llm_call(
        self,
        messages: List[Dict],
        stream: bool,
        stream_callback: Optional[Callable[[ResponseData], None]],
        message_type: MessageType = MessageType.CONTENT,
        enable_thinking: bool = False
    ) -> str:
        """执行 LLM 调用

        :param messages: 消息列表
        :param stream: 是否流式
        :param stream_callback: 流式回调
        :param message_type: 消息类型
        :param enable_thinking: 是否启用思考
        :return: LLM 响应
        """
        response = await self.llm_client.chat_completion(
            messages=messages,
            stream=stream,
            enable_thinking=enable_thinking
        )

        if hasattr(response, '__aiter__'):
            content_parts = []
            async for chunk in response:
                if stream_callback:
                    await self._stream_output(
                        stream_callback,
                        message_type,
                        chunk.delta
                    )
                content_parts.append(chunk.delta)
            return ''.join(content_parts)
        else:
            return response.content

    async def _stream_output(
        self,
        stream_callback: Callable[[ResponseData], None],
        message_type: MessageType,
        data
    ) -> None:
        """流式输出

        :param stream_callback: 流式回调
        :param message_type: 消息类型
        :param data: 数据
        """
        if stream_callback:
            response = ResponseData(message_type=message_type, data=data)
            if hasattr(stream_callback, '__call__'):
                await stream_callback(response)

    def _parse_execution_result(self, response: str) -> Dict:
        """解析执行结果

        :param response: LLM 响应
        :return: 解析后的结果
        """
        try:
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)

                action = data.get("action", {})
                return {
                    "tool_name": action.get("tool_name"),
                    "arguments": action.get("arguments", {}),
                    "reasoning": data.get("reasoning", "")
                }
        except (json.JSONDecodeError, KeyError):
            pass

        return {
            "tool_name": None,
            "arguments": {},
            "reasoning": "parsing failed"
        }

    async def stream_tool_result(
        self,
        stream_callback: Callable[[ResponseData], None],
        tool_name: str,
        observation: Observation
    ) -> None:
        """流式输出工具结果

        :param stream_callback: 流式回调
        :param tool_name: 工具名称
        :param observation: 观察结果
        """
        result_info = {
            "tool_name": tool_name,
            "success": observation.success,
            "content": observation.content
        }
        await self._stream_output(
            stream_callback,
            MessageType.TOOL_RESULT,
            result_info
        )
