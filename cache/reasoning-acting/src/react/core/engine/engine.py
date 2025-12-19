"""ReAct Engine

This module implements the ReAct (Reasoning and Acting) reasoning engine.
The engine uses two-stage mode (planning + execution) for enhanced reasoning.
"""

import time
from typing import Any, Callable, Dict, List, Optional

from react.config.react import ReActConfig
from react.core.engine.execution import Executor
from react.core.engine.planning import Planner
from react.llm.client import LLMClient
from react.memory.memory import Memory
from react.model.execution import ExecutionResult
from react.model.reasoning import Action, Observation, ReasoningStep, Thought
from react.model.response import MessageType, ResponseData
from react.model.tool import ToolCall


class ReActEngine:
    """ReAct Reasoning Engine

    Implements the think-act-observe reasoning cycle
    """

    def __init__(
        self,
        llm_client: LLMClient,
        mcp_manager,
        config=None,
        react_config: Optional[ReActConfig] = None,
        memory: Optional[Memory] = None
    ) -> None:
        """Initialize the engine

        :param llm_client: LLM client
        :param mcp_manager: MCP manager
        :param config: Configuration
        :param react_config: ReAct engine configuration
        :param memory: Short-term memory manager
        """
        self.llm_client: LLMClient = llm_client
        self.mcp_manager = mcp_manager
        self.config = config
        self.react_config = react_config or ReActConfig()
        self._tools: List[Any] = []
        self._max_steps = self.react_config.max_execution_steps
        self._current_state = "idle"
        self.memory = memory or Memory()

        self.planner = Planner(
            llm_client=llm_client,
            config=self.react_config,
            tools=self._tools
        )

        self.executor = Executor(
            llm_client=llm_client,
            config=self.react_config,
            tools=self._tools,
            mcp_manager=mcp_manager
        )

    def update_tools(self, tools: List[Any]) -> None:
        """Update tools list

        :param tools: Tools list
        """
        self._tools = tools
        self.planner.tools = tools
        self.executor.tools = tools

    async def execute(
        self,
        query: str,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> ExecutionResult:
        """Execute reasoning using two-stage mode

        :param query: User question
        :param stream_callback: Stream callback
        :return: Execution result
        """
        await self.memory.add_conversation(
            role="user",
            content=query,
            metadata={"step_count": 0}
        )

        result = await self._execute_two_stage(query, stream_callback)

        await self.memory.add_conversation(
            role="assistant",
            content=result.answer,
            metadata={
                "execution_time": result.execution_time,
                "tool_calls": len(result.tools_used)
            }
        )

        return result

    async def _execute_two_stage(
        self,
        query: str,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> ExecutionResult:
        """Execute reasoning using two-stage mode

        :param query: User question
        :param stream_callback: Stream callback
        :return: Execution result
        """
        start_time = time.time()
        reasoning_steps: List[ReasoningStep] = []
        tools_used: List[ToolCall] = []
        final_answer = ""

        for _ in range(self._max_steps):
            step_result = await self._process_step(
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

    async def _process_step(
        self,
        query: str,
        reasoning_steps: List[ReasoningStep],
        stream_callback: Optional[Callable[[ResponseData], None]]
    ) -> Dict:
        """Process a single reasoning step

        :param query: User question
        :param reasoning_steps: Reasoning history
        :param stream_callback: Stream callback
        :return: Step processing result
        """
        memory_context = await self.memory.build_context_summary(
            conversation_limit=3,
            tool_call_limit=3
        )

        history_dicts = [
            {
                "thought": step.thought.content if step.thought else "",
                "action": {
                    "type": step.action.type if step.action else "unknown",
                    "tool_name": step.action.tool_name if step.action else None
                },
                "observation": {
                    "content": step.observation.content if step.observation else None
                }
            }
            for step in reasoning_steps
        ]

        planning_result = await self.planner.plan(
            query=query,
            history=history_dicts,
            memory_context=memory_context,
            stream_callback=stream_callback
        )

        if planning_result["action"] == "direct_answer":
            answer = await self.executor.generate_answer(
                query=query,
                history=history_dicts,
                planning_result=planning_result,
                stream_callback=stream_callback
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
            tool_call_result = await self._execute_tool_call(
                planning_result=planning_result,
                query=query,
                stream_callback=stream_callback
            )

            if tool_call_result is None:
                return {
                    'is_finish': False,
                    'step': self._create_reasoning_step(
                        thought=planning_result["thought"],
                        action=Action(type="finish"),
                        observation=Observation(
                            content="Failed to extract tool name",
                            tool_name="",
                            success=False
                        )
                    ),
                    'has_tool_call': False
                }

            tool_call, observation = tool_call_result

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

    async def _execute_tool_call(
        self,
        planning_result: Dict,
        query: str,
        stream_callback: Optional[Callable[[ResponseData], None]]
    ) -> Optional[tuple[ToolCall, Observation]]:
        """Execute tool call

        :param planning_result: Planning result
        :param query: User query
        :param stream_callback: Stream callback
        :return: (ToolCall, Observation) or None
        """
        tool_call_data = await self.executor.generate_tool_call(
            planning_result=planning_result,
            query=query,
            stream_callback=stream_callback
        )

        tool_name = tool_call_data["tool_name"]
        if not tool_name:
            tool_name = planning_result.get("tool_name", "")

        if not tool_name:
            return None

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

        observation = await self.executor.execute_tool_call(
            tool_name=tool_name,
            arguments=tool_call_data["arguments"],
            stream_callback=stream_callback
        )

        if stream_callback:
            await self.executor.stream_tool_result(
                stream_callback=stream_callback,
                tool_name=tool_name,
                observation=observation
            )

        await self.memory.add_tool_execution(
            tool_name=tool_name,
            arguments=tool_call_data["arguments"],
            result=observation.content,
            success=observation.success
        )

        return tool_call, observation

    def _create_reasoning_step(
        self,
        thought: str,
        action: Action,
        observation: Optional[Observation] = None
    ) -> ReasoningStep:
        """Create a reasoning step

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

    async def _stream_output(
        self,
        stream_callback: Optional[Callable[[ResponseData], None]],
        message_type: MessageType,
        data
    ) -> None:
        """Stream output

        :param stream_callback: Stream callback
        :param message_type: Message type
        :param data: Data
        """
        if stream_callback:
            import inspect
            response = ResponseData(message_type=message_type, data=data)
            if inspect.iscoroutinefunction(stream_callback):
                await stream_callback(response)
            else:
                stream_callback(response)
