"""短期记忆管理器

此模块实现了一个轻量级的短期记忆系统，用于存储和检索
对话历史和工具调用记录。
"""

from datetime import datetime
from typing import Dict, List, Optional


class Memory:
    """短期记忆管理器

    负责存储和检索对话历史中的短期记忆。
    """

    def __init__(self, max_size: int = 100) -> None:
        """初始化记忆管理器

        :param max_size: 最大记忆条目数
        """
        self.max_size = max_size
        self.created_at = datetime.now()
        self.conversation_history: List[Dict] = []
        self.tool_history: List[Dict] = []

    async def add_conversation(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """添加对话消息

        :param role: 消息角色
        :param content: 消息内容
        :param metadata: 可选元数据
        """
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": role,
            "content": content,
            "metadata": metadata or {}
        })

        if len(self.conversation_history) + len(self.tool_history) > self.max_size:
            await self._trim()

    async def add_tool_execution(
        self,
        tool_name: str,
        arguments: Dict,
        result: str,
        success: bool,
        metadata: Optional[Dict] = None
    ) -> None:
        """添加工具调用记录

        :param tool_name: 工具名称
        :param arguments: 调用参数
        :param result: 执行结果
        :param success: 执行是否成功
        :param metadata: 可选元数据
        """
        self.tool_history.append({
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "success": success,
            "metadata": metadata or {}
        })

        if len(self.conversation_history) + len(self.tool_history) > self.max_size:
            await self._trim()

    async def _trim(self) -> None:
        """修剪记忆长度"""
        conv_keep = int(self.max_size * 0.7)
        tool_keep = self.max_size - conv_keep

        self.conversation_history = self.conversation_history[-conv_keep:]
        self.tool_history = self.tool_history[-tool_keep:]

    async def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """获取最近的对话历史

        :param limit: 返回消息数量限制
        :return: 对话历史列表
        """
        return self.conversation_history[-limit:] if limit > 0 else []

    async def get_recent_tool_calls(self, limit: int = 10) -> List[Dict]:
        """获取最近的工具调用记录

        :param limit: 返回记录数量限制
        :return: 工具历史列表
        """
        return self.tool_history[-limit:] if limit > 0 else []

    async def build_context_summary(
        self,
        conversation_limit: int = 5,
        tool_call_limit: int = 5
    ) -> str:
        """构建对话上下文摘要

        :param conversation_limit: 包含的对话数量
        :param tool_call_limit: 包含的工具调用数量
        :return: 格式化的上下文摘要
        """
        context_parts = []

        recent_conversations = await self.get_recent_conversations(conversation_limit)
        if recent_conversations:
            context_parts.append("Recent conversations:")
            for conv in recent_conversations:
                role = conv["type"].capitalize()
                content = conv["content"][:100]
                context_parts.append(f"  {role}: {content}")

        recent_tools = await self.get_recent_tool_calls(tool_call_limit)
        if recent_tools:
            context_parts.append("Recent tool calls:")
            for tool in recent_tools:
                status = "✓" if tool["success"] else "✗"
                context_parts.append(
                    f"  {status} {tool['tool_name']}: {tool['result'][:100]}"
                )

        return "\n".join(context_parts) if context_parts else "No history"

    async def clear(self) -> None:
        """清空所有记忆"""
        self.conversation_history.clear()
        self.tool_history.clear()

    def get_stats(self) -> Dict:
        """获取记忆统计信息

        :return: 统计信息字典
        """
        return {
            "conversation_count": len(self.conversation_history),
            "tool_call_count": len(self.tool_history),
            "total_entries": len(self.conversation_history) + len(self.tool_history),
            "max_size": self.max_size,
            "created_at": self.created_at.isoformat()
        }
