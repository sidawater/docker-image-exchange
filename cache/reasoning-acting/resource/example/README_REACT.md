# ReAct Engine 使用指南

本目录包含 ReAct 引擎的示例代码，展示如何使用新的模块化架构。

## 📁 文件说明

### 1. `demo_react_simple.py` ⭐ **推荐入门**
最简单的 ReAct 引擎演示，包含：
- 内置 Mock LLM 客户端（无需外部 LLM 服务）
- 内置测试 MCP 服务器（提供 4 个测试工具）
- 完整的 ReAct 引擎功能演示
- 内存、流式输出等特性

**运行方式**：
```bash
cd /data/home/solgeo/projects/reasoning-acting
python resource/example/demo_react_simple.py
```

### 2. `demo_react.py`
完整的 ReAct 引擎演示，需要：
- 外部 LLM 服务（vLLM OpenAI 兼容）
- 外部 MCP 服务器

**运行方式**：
```bash
# 1. 配置 LLM 和 MCP 服务器地址
# 2. 运行
python resource/example/demo_react.py
```

### 3. 其他示例文件
- `demo_llm.py` - LLM 客户端使用
- `demo_mcp.py` - MCP 管理器使用
- `demo_mcp_client.py` - MCP 客户端使用
- `demo_mcp_simple.py` - 简单的 MCP 测试

## 🏗️ 模块化架构

### 核心组件

```
┌─────────────────────────────────────┐
│         ReActEngine                 │
│  (统筹协调)                         │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┬──────────────┐
       │                │              │
   ┌───▼───┐      ┌────▼────┐    ┌───▼───┐
   │Planner│      │Executor │    │Memory │
   │规划阶段│      │执行阶段 │    │记忆模块│
   └───┬───┘      └────┬────┘    └───┬───┘
       │               │              │
       └───────────────┼──────────────┘
                       │
                ┌──────▼──────┐
                │  Tools      │
                │ (MCP)       │
                └─────────────┘
```

### 1. Memory Module (`src/react/memory/memory.py`)
**职责**: 短期记忆管理
**功能**:
- 存储对话历史
- 存储工具调用记录
- 自动记忆修剪
- 构建上下文摘要

```python
from react.memory.memory import Memory

memory = Memory(max_size=100)
await memory.add_conversation("user", "Hello")
await memory.add_tool_execution("add", {"a": 1, "b": 2}, "Result: 3", True)
summary = await memory.build_context_summary()
```

### 2. Planning Phase (`src/react/core/engine/planning.py`)
**职责**: 规划决策
**功能**:
- 分析当前情况
- 决定下一步行动（直接回答 or 工具调用）
- 支持流式思考输出

```python
from react.core.engine.planning import Planner

planner = Planner(llm_client, config, tools)
result = await planner.plan(
    query="What is 2+2?",
    history=[],
    memory_context="Previous context...",
    stream_callback=my_callback
)
```

### 3. Execution Phase (`src/react/core/engine/execution.py`)
**职责**: 执行和回答生成
**功能**:
- 执行工具调用
- 生成工具调用参数
- 生成最终回答

```python
from react.core.engine.execution import Executor

executor = Executor(llm_client, config, tools, mcp_manager)
answer = await executor.generate_answer(query, history, planning_result)
```

### 4. Engine Module (`src/react/core/engine/engine.py`)
**职责**: 统筹协调
**功能**:
- 初始化所有组件
- 执行推理循环
- 管理推理步骤
- 集成记忆功能

```python
from react.core.engine.engine import ReActEngine

engine = ReActEngine(
    llm_client=llm_client,
    mcp_manager=mcp_manager,
    react_config=config,
    memory=memory
)

result = await engine.execute("What is 2+2?")
```

## 🚀 快速开始

### 步骤 1: 初始化组件

```python
import asyncio
from react.llm import llm_manager, VllmOpenaiConfig
from react.config.mcp import MCPConfig
from react.config.react import ReActConfig
from react.mcp.client.manager import MCPClientManager
from react.core.engine.engine import ReActEngine
from react.memory.memory import Memory

async def main():
    # 1. 创建 LLM 客户端
    llm_config = VllmOpenaiConfig(
        provider="vllm_openai",
        model="your_model",
        api_key="your_key",
        base_url="http://your-llm:8001"
    )
    llm_client = llm_manager.create("vllm_text", llm_config)

    # 2. 创建 MCP 管理器
    mcp_config = MCPConfig(
        servers=[MCPConfig.Server(
            name="my_server",
            type="sse",
            url="http://your-mcp:3000"
        )]
    )
    mcp_manager = MCPClientManager(mcp_config)
    await mcp_manager.initialize()

    # 3. 创建 ReAct 引擎
    react_config = ReActConfig(max_execution_steps=10)
    memory = Memory(max_size=100)
    engine = ReActEngine(
        llm_client=llm_client,
        mcp_manager=mcp_manager,
        react_config=react_config,
        memory=memory
    )

    # 4. 更新工具列表
    tools = mcp_manager.get_tools()
    engine.update_tools(tools)

    # 5. 执行查询
    result = await engine.execute("What is 2+2?")
    print(f"Answer: {result.answer}")

    # 6. 清理
    await mcp_manager.close()
    await llm_client.close()

asyncio.run(main())
```

### 步骤 2: 使用流式输出

```python
from react.model.response import ResponseData

async def stream_callback(response: ResponseData):
    if response.message_type.value == "thinking":
        print(f"Thinking: {response.data}", end="")
    elif response.message_type.value == "content":
        print(f"\nAnswer: {response.data}")
    elif response.message_type.value == "tool_call":
        print(f"\nUsing tool: {response.data['tool_name']}")
    elif response.message_type.value == "tool_result":
        print(f"Tool result: {response.data['content']}")

result = await engine.execute(
    "Calculate 5 * 6",
    stream_callback=stream_callback
)
```

### 步骤 3: 检查记忆

```python
# 查看记忆统计
stats = memory.get_stats()
print(f"Total entries: {stats['total_entries']}")

# 获取最近的对话
recent = await memory.get_recent_conversations(limit=5)
for conv in recent:
    print(f"{conv['type']}: {conv['content']}")

# 获取最近的工具调用
tools = await memory.get_recent_tool_calls(limit=5)
for tool in tools:
    print(f"{tool['tool_name']}: {tool['result']}")
```

## 🧪 测试用例

### 用例 1: 基本查询（无需工具）
```python
result = await engine.execute("What is the capital of France?")
# 引擎会直接调用 LLM 回答
```

### 用例 2: 计算查询（需要工具）
```python
result = await engine.execute("What is 25 + 17?")
# 引擎会:
# 1. Planning: 决定需要使用计算工具
# 2. Execution: 调用 add 工具
# 3. 生成最终回答
```

### 用例 3: 多步推理
```python
result = await engine.execute(
    "If I have 5 apples and buy 3 more, then give away 2, how many do I have?"
)
# 引擎会进行多步推理
```

### 用例 4: 记忆测试
```python
await engine.execute("My name is Alice")
await engine.execute("What is my name?")
# 第二次查询应该能记住名字（如果 LLM 支持）
```

## 📊 输出示例

```
============================================================
REACT ENGINE SIMPLE DEMO
============================================================

Features:
  ✓ Modular architecture (Memory, Planning, Execution)
  ✓ Mock LLM client (no external dependencies)
  ✓ Built-in test MCP server
  ✓ Memory persistence
  ✓ Streaming support
============================================================

1. INITIALIZING MOCK LLM CLIENT
============================================================
✓ Mock LLM client created (for testing without external LLM)

2. INITIALIZING MCP MANAGER
============================================================
✓ MCP manager initialized
  Connected to: http://localhost:3002
  Discovered 4 tools:
    - echo: Echo back the input message
    - add: Add two numbers
    - multiply: Multiply two numbers
    - get_time: Get current timestamp

3. INITIALIZING REACT ENGINE
============================================================
✓ Memory enabled (max_size=100)
✓ ReAct engine initialized
  Max execution steps: 10
  Stream thoughts: True
  Updated tools: 4 loaded

TEST 1: Basic Query
============================================================

Query: Hello, can you help me?

✓ Answer: Mock response to: Hello, can you help me?...
  Steps: 0
  Time: 0.001s

TEST 2: Calculator Tool
============================================================

Query: What is 25 + 17?

✓ Answer: Mock response to: What is 25 + 17?...
  Tools used: 0
  Time: 0.002s

...
```

## 🔧 配置说明

### ReActConfig
```python
react_config = ReActConfig(
    max_execution_steps=10,    # 最大执行步数
    stream_thoughts=True,      # 是否流式输出思考过程
)
```

### MemoryConfig
```python
memory = Memory(
    max_size=100,              # 最大记忆条目数
)
```

### MCPConfig
```python
mcp_config = MCPConfig(
    servers=[
        MCPConfig.Server(
            name="server_name",
            type="sse",              # 连接类型: sse, stdio, websocket
            url="http://server:3000",
            timeout=30,
        )
    ],
    connection_timeout=30,
    reconnect_attempts=3,
)
```

## ⚠️ 注意事项

1. **代理设置**: 如果使用外部 MCP 服务器，需要取消设置代理环境变量
   ```python
   import os
   for var in ['http_proxy', 'https_proxy', 'all_proxy']:
       os.environ.pop(var, None)
   ```

2. **错误处理**: 实际应用中需要添加适当的错误处理和重试机制

3. **资源清理**: 记得在结束时关闭 LLM 客户端和 MCP 管理器

4. **流式回调**: 确保流式回调函数是异步的（async def）

## 📚 更多信息

- 查看 `demo_react_simple.py` 了解完整示例
- 查看各模块的 docstring 了解详细 API
- 查看 `demo_mcp_simple.py` 了解 MCP 工具测试
