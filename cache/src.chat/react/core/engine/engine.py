"""ReAct Engine

This module implements the ReAct (Reasoning and Acting) reasoning engine.
The engine uses two-stage mode (planning + execution) for enhanced reasoning.
"""

import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Union, AsyncIterator

from react.config.react import ReActConfig
from react.llm.client import LLMClient
from react.model.execution import ExecutionResult
from react.model.reasoning import Action, Observation, ReasoningStep, Thought
from react.model.response import MessageType, ResponseData
from react.model.tool import ToolCall


class ReActEngine:
    """
    ReAct Reasoning Engine

    Implements the think-act-observe reasoning cycle
    """

    def __init__(
        self,
        llm_client: LLMClient,
        mcp_manager,
        config=None,
        react_config: Optional[ReActConfig] = None
    ) -> None:
        """
        Initialize the engine

        :param llm_client: LLM client
        :param mcp_manager: MCP manager
        :param config: Configuration
        :param react_config: ReAct engine configuration
        """
        self.llm_client: LLMClient = llm_client
        self.mcp_manager = mcp_manager
        self.config = config
        self.react_config = react_config or ReActConfig()
        self._tools: List[Any] = []
        self._max_steps = self.react_config.max_execution_steps
        self._current_state = "idle"

    def update_tools(self, tools: List[Any]) -> None:
        """
        Update tools list

        :param tools: Tools list
        """
        self._tools = tools

    def _build_tools_description(self) -> str:
        """
        Build tools description

        :return: Tools description text
        """
        if not self._tools:
            return "No available tools"

        descriptions = []
        for tool in self._tools:
            desc = f"- {tool.name}: {tool.description}"
            if hasattr(tool, 'input_schema') and tool.input_schema:
                params = tool.input_schema.get("properties", {})
                if params:
                    param_str = ", ".join(params.keys())
                    desc += f" (parameters: {param_str})"
            descriptions.append(desc)

        return "\n".join(descriptions)

    def _parse_llm_response(self, content: str) -> tuple[Thought, Action]:
        """
        Parse LLM response

        :param content: Response content
        :return: (Thought, Action)
        """
        try:
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                data = {"thought": content, "action": {"type": "finish"}}

            thought = Thought(
                content=data.get("thought", ""),
                reasoning=data.get("thought", "")
            )

            action_data = data.get("action", {})
            action_type = action_data.get("type", "finish")

            if action_type == "tool_call":
                action = Action(
                    type="tool_call",
                    tool_name=action_data.get("tool_name"),
                    arguments=action_data.get("arguments", {})
                )
            else:
                action = Action(type="finish")

            return thought, action

        except json.JSONDecodeError:
            return Thought(content=content, reasoning=content), Action(type="finish")

    async def _execute_tool(self, tool_name: str, arguments: Dict) -> Observation:
        """
        Execute tool

        :param tool_name: Tool name
        :param arguments: Arguments
        :return: Observation result
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
                content=content_text or "Tool execution successful (no content returned)",
                tool_name=tool_name,
                success=True
            )

        except Exception as e:
            return Observation(
                content=f"Tool execution exception: {str(e)}",
                tool_name=tool_name,
                success=False
            )

    async def _stream_output(
        self,
        stream_callback: Optional[Callable[[ResponseData], None]],
        message_type: MessageType,
        data: Union[str, dict, Any],
        is_error: bool = False
    ) -> None:
        """
        Stream output to callback using ResponseData

        :param stream_callback: Stream callback function
        :param message_type: Type of message
        :param data: Message data
        :param is_error: Whether this is an error message
        """
        if not stream_callback:
            return

        try:
            import inspect
            response = ResponseData(message_type=message_type, data=data)
            if inspect.iscoroutinefunction(stream_callback):
                await stream_callback(response)
            else:
                stream_callback(response)
        except Exception as e:
            if is_error:
                raise

    async def _execute_llm_call(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        stream_callback: Optional[Callable[[ResponseData], None]],
        message_type: MessageType = MessageType.CONTENT
    ) -> str:
        """
        Execute LLM call with optional streaming support

        :param messages: Messages for LLM
        :param stream_callback: Stream callback function
        :param message_type: Type of message for streaming
        :return: Full response content
        """
        try:
            response = await self.llm_client.chat_completion(messages, stream=stream)

            if isinstance(response, AsyncIterator):
                content_parts = []
                async for chunk in response:
                    await self._stream_output(
                        stream_callback, message_type, chunk.delta
                    )
                    content_parts.append(chunk.delta)
                return ''.join(content_parts)
            else:
                return response.content

        except Exception:
            raise

    async def execute(
        self,
        query: str,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> ExecutionResult:
        """
        Execute reasoning using two-stage mode

        :param query: User question
        :param stream_callback: Stream callback
        :return: Execution result
        """
        return await self._execute_two_stage(query, stream_callback)

    async def _execute_two_stage(
        self,
        query: str,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> ExecutionResult:
        """
        Execute reasoning using two-stage mode (planning + execution)

        :param query: User question
        :param stream_callback: Stream callback
        :return: Execution result
        """
        start_time = time.time()
        reasoning_steps: List[ReasoningStep] = []
        tools_used: List[ToolCall] = []
        final_answer = ""

        for _ in range(self._max_steps):
            step_result = await self._process_step_two_stage(
                query, reasoning_steps, stream_callback
            )

            if step_result['is_finish']:
                final_answer = step_result['answer']
                reasoning_steps.append(step_result['step'])
                break

            if step_result['has_tool_call']:
                tools_used.append(step_result['tool_call'])
                reasoning_steps.append(step_result['step'])

        if not final_answer and reasoning_steps:
            final_answer = reasoning_steps[-1].thought.content

        return ExecutionResult(
            answer=final_answer,
            reasoning_steps=reasoning_steps,
            tools_used=tools_used,
            execution_time=time.time() - start_time,
            mode="two_stage"
        )

    async def _process_step_two_stage(
        self,
        query: str,
        reasoning_steps: List[ReasoningStep],
        stream_callback: Optional[Callable[[ResponseData], None]]
    ) -> Dict:
        """
        Process a single reasoning step in two-stage mode

        :param query: User question
        :param reasoning_steps: Reasoning history
        :param stream_callback: Stream callback
        :return: Step processing result
        """
        planning_result = await self._planning_phase(
            query, reasoning_steps, stream_callback
        )

        if planning_result["action"] == "direct_answer":
            answer = await self._answer_phase(
                query, reasoning_steps, planning_result, stream_callback
            )
            return {
                'is_finish': True,
                'answer': answer,
                'step': self._create_reasoning_step(
                    thought=planning_result["thought"],
                    action=Action(type="finish")
                ),
                'has_tool_call': False
            }

        elif planning_result["action"] == "tool_call":
            tool_call, observation = await self._execute_tool_call_two_stage(
                planning_result, stream_callback
            )
            return {
                'is_finish': False,
                'step': self._create_reasoning_step(
                    thought=planning_result["thought"],
                    action=Action(
                        type="tool_call",
                        tool_name=tool_call.tool_name,
                        arguments=tool_call.arguments
                    ),
                    observation=observation
                ),
                'has_tool_call': True,
                'tool_call': tool_call
            }

        return {
            'is_finish': False,
            'step': None,
            'has_tool_call': False
        }

    async def _execute_tool_call_two_stage(
        self,
        planning_result: Dict,
        stream_callback: Optional[Callable[[ResponseData], None]]
    ) -> tuple[ToolCall, Observation]:
        """
        Execute tool call in two-stage mode

        :param planning_result: Planning phase result
        :param stream_callback: Stream callback
        :return: (ToolCall, Observation)
        """
        tool_call_data = await self._execution_phase(
            planning_result, stream_callback
        )

        tool_name = tool_call_data["tool_name"]
        if not tool_name:
            tool_name = planning_result.get("tool_name", "unknown")

        await self._stream_output(
            stream_callback,
            MessageType.TOOL_CALL,
            {
                "tool_name": tool_name,
                "arguments": tool_call_data["arguments"]
            }
        )
        tool_call = ToolCall(
            tool_name=tool_name,
            arguments=tool_call_data["arguments"]
        )
        observation = await self._execute_tool(tool_name, tool_call_data["arguments"])

        if stream_callback:
            await self._stream_tool_result(
                stream_callback,
                tool_name,
                observation
            )

        return tool_call, observation

    async def _planning_phase(
        self,
        query: str,
        history: List[ReasoningStep],
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> Dict:
        """
        Planning phase: Think about the next step without generating structure

        :param query: User question
        :param history: Reasoning history
        :param stream_callback: Stream callback
        :return: Planning result
        """
        messages = self._build_planning_messages(query, history)

        thought_content = []
        if stream_callback and self.react_config.stream_thoughts:
            await self._stream_output(
                stream_callback, MessageType.THINKING, "thinking"
            )

            full_response = await self._execute_llm_call(
                messages,
                stream=True,
                stream_callback=stream_callback,
                message_type=MessageType.THINKING
            )
            thought_content = [full_response] if full_response else []
        else:
            full_response = await self._execute_llm_call(
                messages,
                stream=False,
                stream_callback=stream_callback
            )
            thought_content = [full_response] if full_response else []

        return self._parse_planning_result(''.join(thought_content))

    async def _execution_phase(
        self,
        planning_result: Dict,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> Dict:
        """
        Execution phase: Generate structured tool call

        :param planning_result: Planning phase result
        :param stream_callback: Stream callback
        :return: Tool call data
        """
        messages = self._build_execution_messages(planning_result)

        tool_name = planning_result.get('tool_name', 'unknown')
        await self._stream_output(
            stream_callback,
            MessageType.STATUS,
            {"status": "preparing_tool_call", "tool_name": tool_name}
        )

        response = await self._execute_llm_call(
            messages,
            stream=False,
            stream_callback=stream_callback
        )

        return self._parse_execution_result(response)

    async def _answer_phase(
        self,
        query: str,
        history: List[ReasoningStep],
        planning_result: Dict,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> str:
        """
        Answer phase: Generate final answer based on reasoning history

        :param query: User question
        :param history: Reasoning history
        :param planning_result: Planning result with analysis
        :param stream_callback: Stream callback
        :return: Final answer
        """
        context_parts = []
        for step in history:
            if step.action and step.action.type == "tool_call":
                context_parts.append(f"Called {step.action.tool_name}")
                if step.observation:
                    context_parts.append(f"Result: {step.observation.content}")

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
            messages,
            stream=True,
            stream_callback=stream_callback,
            message_type=MessageType.CONTENT
        )

        return answer

    def _build_planning_messages(
        self,
        query: str,
        history: List[ReasoningStep]
    ) -> List[Dict[str, str]]:
        """Build messages for planning phase in two-stage mode.

        :param query: User question
        :param history: Reasoning history
        :return: Messages list
        """
        tools_desc = self._build_tools_description()

        summary = self._build_history_summary(history)

        messages = [
            {
                "role": "system",
                "content": self.react_config.prompts.planner.TEMPLATE.format(
                    summary=summary,
                    tools=tools_desc,
                    analysis="Reasoning based on the above information",
                    tool_name="{tool_name}"
                )
            },
            {
                "role": "user",
                "content": f"Question: {query}"
            }
        ]

        return messages

    def _build_execution_messages(self, planning_result: Dict) -> List[Dict[str, str]]:
        """Build messages for execution phase in two-stage mode.

        :param planning_result: Planning result
        :return: Messages list
        """
        tools_desc = self._build_tools_description()

        messages = [
            {
                "role": "system",
                "content": self.react_config.prompts.executor.TEMPLATE.format(
                    tool_descriptions=tools_desc,
                    planning_conclusion=planning_result.get('raw_conclusion', ''),
                    tool_name="{tool_name}",
                    parameter_key_value_pairs="{parameter_key_value_pairs}"
                )
            },
            {
                "role": "user",
                "content": "Please generate JSON format tool call parameters"
            }
        ]

        return messages

    def _build_history_summary(self, history: List[ReasoningStep]) -> str:
        """
        Build summary of reasoning history

        :param history: Reasoning history
        :return: Summary text
        """
        if not history:
            return "Initial state, no reasoning has been performed yet"

        summary_parts = []
        for i, step in enumerate(history[-3:], 1):
            if step.action and step.action.type == "tool_call":
                summary_parts.append(
                    f"Step {i}: Called {step.action.tool_name} tool"
                )
                if step.observation:
                    summary_parts.append(
                        f"Result: {step.observation.content[:100]}..."
                    )

        return "\n".join(summary_parts) if summary_parts else "Some reasoning steps have been performed"

    def _parse_planning_result(self, content: str) -> Dict:
        """
        Parse planning phase text output

        :param content: Planning output content
        :return: Parsed result
        """
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

    def _parse_execution_result(self, response: str) -> Dict:
        """
        Parse execution phase JSON output

        :param response: Execution output
        :return: Parsed tool call data
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

    def _create_reasoning_step(
        self,
        thought: str,
        action: Action,
        observation: Optional[Observation] = None
    ) -> ReasoningStep:
        """
        Create a reasoning step

        :param thought: Thought content
        :param action: Action
        :param observation: Optional observation
        :return: Reasoning step
        """
        return ReasoningStep(
            thought=Thought(content=thought, reasoning=thought),
            action=action,
            observation=observation
        )

    async def _stream_tool_result(
        self,
        stream_callback: Callable[[ResponseData], None],
        tool_name: str,
        observation: Observation
    ) -> None:
        """
        Stream tool result

        :param stream_callback: Stream callback
        :param tool_name: Tool name
        :param observation: Observation
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
