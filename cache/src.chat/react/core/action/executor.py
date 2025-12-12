"""Action Executor"""

from react.model.reasoning import Action, Observation
from react.model.execution import ReActState


class ActionExecutor:
    """Action executor"""

    def __init__(self, mcp_manager) -> None:
        self.mcp_manager = mcp_manager

    async def execute_action(
        self,
        action: Action,
        context: ReActState
    ) -> 'ActionResult':
        """Execute action based on type.

        :param action: Action to execute
        :param context: ReAct state context
        :return: ActionResult with observation
        """
        if action.type == "tool_call":
            return await self._execute_tool_call(action)
        elif action.type == "finish":
            return ActionResult(action=action, observation=None)
        else:
            return ActionResult(
                action=action,
                observation=Observation(
                    content=f"Unknown action type: {action.type}",
                    tool_name=action.tool_name,
                    success=False
                )
            )

    async def _execute_tool_call(self, action: Action) -> 'ActionResult':
        """Execute tool call action.

        :param action: Tool call action
        :return: ActionResult with tool execution observation
        """
        tool_name = action.tool_name
        arguments = action.arguments

        try:
            result = await self.mcp_manager.call_tool(tool_name, arguments)

            if result.is_error:
                observation = Observation(
                    content=f"Tool execution error: {result.error_message}",
                    tool_name=tool_name,
                    success=False
                )
            else:
                content_text = ""
                for item in result.content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            content_text += item.get("text", "")
                    else:
                        content_text += str(item)

                observation = Observation(
                    content=content_text or "Tool execution successful (no content returned)",
                    tool_name=tool_name,
                    success=True
                )

            return ActionResult(action=action, observation=observation)

        except Exception as e:
            observation = Observation(
                content=f"Tool execution exception: {str(e)}",
                tool_name=tool_name,
                success=False
            )
            return ActionResult(action=action, observation=observation)


class ActionResult:
    """Action result"""

    def __init__(
        self,
        action: Action,
        observation: Observation | None
    ) -> None:
        self.action = action
        self.observation = observation
