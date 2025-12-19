"""Planning Phase 模块

实现 ReAct 引擎的 Planning Phase，负责分析当前情况并决定下一步行动。
"""

from typing import Callable, Dict, List, Optional

from react.config.react import ReActConfig
from react.llm.client import LLMClient
from react.model.response import MessageType, ResponseData


class Planner:
    """规划器

    负责分析当前情况，决定下一步行动（调用工具或直接回答）。
    """

    def __init__(
        self,
        llm_client: LLMClient,
        config: ReActConfig,
        tools: List
    ) -> None:
        """初始化规划器

        :param llm_client: LLM 客户端
        :param config: ReAct 配置
        :param tools: 可用工具列表
        """
        self.llm_client = llm_client
        self.config = config
        self.tools = tools

    async def plan(
        self,
        query: str,
        history: List[Dict],
        memory_context: str,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> Dict:
        """执行规划

        :param query: 用户查询
        :param history: 推理历史
        :param memory_context: 记忆上下文
        :param stream_callback: 流式回调
        :return: 规划结果
        """
        messages = self._build_messages(query, history, memory_context)

        if stream_callback and self.config.stream_thoughts:
            full_response = await self._execute_llm_call(
                messages=messages,
                stream=True,
                stream_callback=stream_callback,
                message_type=MessageType.THINKING
            )
        else:
            full_response = await self._execute_llm_call(
                messages=messages,
                stream=False,
                stream_callback=stream_callback
            )

        return self._parse_result(full_response)

    def _build_messages(
        self,
        query: str,
        history: List[Dict],
        memory_context: str
    ) -> List[Dict]:
        """构建消息

        :param query: 用户查询
        :param history: 推理历史
        :param memory_context: 记忆上下文
        :return: 消息列表
        """
        summary = self._build_history_summary(history)

        return [
            {
                "role": "system",
                "content": self.config.prompts.planner.TEMPLATE.format(
                    summary=f"{summary}\n\nMemory Context:\n{memory_context}",
                    tools=self._build_tools_description(),
                    analysis="Reasoning based on the above information",
                    tool_name="{tool_name}"
                )
            },
            {
                "role": "user",
                "content": f"Question: {query}"
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

    def _build_history_summary(self, history: List[Dict]) -> str:
        """构建历史摘要

        :param history: 推理历史
        :return: 摘要文本
        """
        if not history:
            return "Initial state, no reasoning has been performed yet"

        summary_parts = []
        for i, step in enumerate(history[-3:], 1):
            if step.get("action") and step["action"].get("type") == "tool_call":
                summary_parts.append(
                    f"Step {i}: Called {step['action']['tool_name']} tool"
                )
                if step.get("observation"):
                    obs_content = step["observation"]["content"]
                    summary_parts.append(
                        f"Result: {obs_content[:100]}..."
                    )

        return "\n".join(summary_parts) if summary_parts else "Some reasoning steps have been performed"

    async def _execute_llm_call(
        self,
        messages: List[Dict],
        stream: bool,
        stream_callback: Optional[Callable[[ResponseData], None]],
        message_type: MessageType = MessageType.CONTENT
    ) -> str:
        """执行 LLM 调用

        :param messages: 消息列表
        :param stream: 是否流式
        :param stream_callback: 流式回调
        :param message_type: 消息类型
        :return: LLM 响应
        """
        response = await self.llm_client.chat_completion(
            messages=messages,
            stream=stream,
            enable_thinking=True
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

    def _parse_result(self, content: str) -> Dict:
        """解析结果

        :param content: LLM 响应内容
        :return: 解析后的结果
        """
        import re

        lines = content.strip().split('\n')
        thought = ""
        conclusion = ""
        tool_name = None

        for line in lines:
            if line.startswith("My analysis:"):
                thought = line.replace("My analysis:", "").strip()
            elif line.startswith("Conclusion:"):
                conclusion_line = line.replace("Conclusion:", "").strip()
                conclusion = conclusion_line

                if "call" in conclusion_line.lower():
                    match = re.search(r"call[【\s]+(\w+)", conclusion_line.lower())
                    if match:
                        tool_name = match.group(1)

        if tool_name:
            return {
                "thought": thought,
                "action": "tool_call",
                "tool_name": tool_name,
                "raw_conclusion": conclusion
            }
        else:
            return {
                "thought": thought or content,
                "action": "direct_answer",
                "raw_conclusion": conclusion
            }
