# Redis Manager - Improved Design

## 🎯 解决的问题

基于 `/resource/plans/db/configuration_analysis.md` 中识别的配置不一致问题，以及 redis-py 5.2 到 7.1 版本升级带来的 API 变化，我们重新设计了 Redis Manager。

## 📊 问题总结

### 1. 配置不一致（高优先级）
- **文档定义**: 15+ 个独立参数
- **原始实现**: 仅接受 `url` 和 `**kwargs`
- **影响**: 开发者无法在 IDE 中查看可用选项

### 2. Redis 版本兼容性问题
- **redis 5.2**: `ping(message=None)` - 可选消息参数
- **redis 7.x**: `ping(**kwargs)` - 仅关键字参数
- **问题**: `ping("message")` 在 7.x 中会失败

### 3. API 清晰度
- 无类型提示
- 无明确参数文档
- 难以理解可用选项

## ✨ 解决方案

### 新架构

所有参数直接在 `RedisManager.init()` 方法中定义，无需单独的 config 模块：

```python
class RedisManager:
    async def init(
        self,
        url: str,
        max_connections: int = 50,
        encoding: str = "utf-8",
        decode_responses: bool = True,
        socket_connect_timeout: int = 5,
        socket_timeout: int = 5,
        health_check_interval: int = 30,
        retry_on_timeout: bool = True,
    ) -> None:
        """初始化 Redis 连接"""
```

### 使用示例

#### 基础用法

```python
from sengine.db.redis import RedisManager

# 创建管理器
redis_manager = RedisManager()

# 初始化（只需要 URL）
await redis_manager.init(url="redis://localhost:6379/0")

# 使用客户端
client = redis_manager.client
await client.set("key", "value")
value = await client.get("key")
```

#### 完整参数配置

```python
from sengine.db.redis import RedisManager

redis_manager = RedisManager()

# 使用所有参数
await redis_manager.init(
    url="redis://localhost:6379/0",
    max_connections=100,
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=10,
    socket_timeout=10,
    health_check_interval=60,
    retry_on_timeout=False,
)

client = redis_manager.client
```

#### 局部参数配置

```python
from sengine.db.redis import RedisManager

redis_manager = RedisManager()

# 只指定需要的参数（其他使用默认值）
await redis_manager.init(
    url="redis://localhost:6379/0",
    max_connections=100,
    socket_connect_timeout=10,
)

client = redis_manager.client
```

#### 全局实例使用

```python
from sengine.db.redis import get_redis_manager

# 获取全局实例
redis_manager = get_redis_manager()

# 初始化
await redis_manager.init(url="redis://localhost:6379/0")

# 使用
client = redis_manager.client
await client.set("global_key", "global_value")
```

## 📋 配置参数

支持以下参数（所有参数都有类型提示和默认值）：

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| url | str | - | **必需** - Redis 连接 URL |
| max_connections | int | 50 | 连接池中的最大连接数 |
| encoding | str | "utf-8" | 字符串编码 |
| decode_responses | bool | True | 自动解码响应为字符串 |
| socket_connect_timeout | int | 5 | 连接超时（秒） |
| socket_timeout | int | 5 | 套接字超时（秒） |
| health_check_interval | int | 30 | 健康检查间隔（秒） |
| retry_on_timeout | bool | True | 超时时重试 |

## 🔄 Redis 版本兼容性

### Ping 方法处理

Ping 方法现在处理 redis-py 5.x 和 7.x 的差异：

```python
# 测试连接，使用 ping() 无参数（兼容 redis-py 5.x 和 7.x）
try:
    ping_result = self._client.ping()
    if inspect.isawaitable(ping_result):
        # 异步模式（5.x 和 7.x）
        await ping_result
    # 同步模式中，结果已经是布尔值
except RedisConnectionError as e:
    await self.close()
    raise RuntimeError(f"Failed to connect to Redis: {e}")
```

**关键点:**
1. ✅ 永远不传递消息参数：`ping()` 而非 `ping("message")`
2. ✅ 如果是可等待的，总是 await 结果
3. ✅ 处理异步和同步上下文
4. ✅ 连接失败时自动清理

### 避免的模式

❌ **不要** 使用消息参数（redis 7.x 中失败）：

```python
await redis_manager.client.ping("test")  # ❌ redis 7.x 中 TypeError
```

✅ **这样做**：

```python
await redis_manager.client.ping()  # ✅ 在 5.x 和 7.x 中都有效
```

## 🧪 测试

运行测试套件验证实现：

```bash
cd /data/home/solgeo/projects/kb-sengine
python test_redis_redesign.py
```

测试包括：
- ✅ RedisManager 基本功能
- ✅ 完整参数初始化
- ✅ 最小参数初始化
- ✅ 局部参数初始化
- ✅ 连接失败处理
- ✅ 双初始化保护

## 📁 文件结构

```
src/sengine/db/redis/
├── __init__.py          # 导出 RedisManager, get_redis_manager
├── client.py            # RedisManager 类，包含所有参数定义
└── README.md            # 本文件
```

## 💡 关键改进

1. **明确参数**: 所有参数在函数签名中直接定义
2. **类型安全**: 完整类型提示支持 IDE
3. **版本兼容**: 与 redis-py 5.2 和 7.x 都兼容
4. **自动连接测试**: 初始化时自动验证连接
5. **错误处理**: 连接失败时自动清理资源
6. **文档完整**: 每个参数都有 Sphinx 风格文档

## 🚀 迁移指南

### 对于新代码

直接使用明确的参数：

```python
from sengine.db.redis import RedisManager

redis_manager = RedisManager()
await redis_manager.init(
    url="redis://localhost:6379/0",
    max_connections=50,
)
```

### 对于现有代码

如果你已经在使用 `await redis_manager.init(url="...")`：
- **无需更改** - 它仍然有效
- 考虑添加其他参数以获得更好的性能

## 🔗 相关文档

- `/resource/plans/db/configuration_analysis.md` - 原始问题分析
- `/resource/plans/db/summary.md` - 执行摘要
