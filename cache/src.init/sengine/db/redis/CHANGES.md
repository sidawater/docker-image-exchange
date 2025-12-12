# Redis Manager - 变更日志

## 📅 2025-12-12 - Redis Manager 重新设计

### 🎯 解决的问题

1. **配置不一致** - 根据 `/resource/plans/db/configuration_analysis.md`
   - 原问题：文档定义15+参数，实现仅接受 `**kwargs`
   - 解决方案：所有参数直接在 `init()` 方法中定义

2. **Redis 版本兼容性** - redis 5.2 vs 7.x
   - 原问题：`ping("message")` 在 7.x 中失败
   - 解决方案：使用 `ping()` 无参数调用

3. **API 清晰度**
   - 原问题：无类型提示，参数不明确
   - 解决方案：完整的类型提示和 Sphinx 风格文档

### ✨ 关键变更

#### 1. init() 方法签名变更

**变更前:**
```python
async def init(self, url: str, **kwargs) -> None:
    connection_kwargs = {
        'decode_responses': True,
        'socket_connect_timeout': 5,
        'retry_on_timeout': True,
        **kwargs
    }
```

**变更后:**
```python
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
```

#### 2. Redis 版本兼容性处理

**变更前:**
```python
await self._client.ping()
```

**变更后:**
```python
ping_result = self._client.ping()
if inspect.isawaitable(ping_result):
    await ping_result
except RedisConnectionError as e:
    await self.close()
    raise RuntimeError(f"Failed to connect to Redis: {e}")
```

#### 3. 移除 config 模块

- ❌ 删除：`src/sengine/db/redis/config.py`
- ✅ 所有参数直接在 `client.py` 中定义
- ✅ 符合"严禁 db 模块直接引用 config 模块"的要求

### 📋 支持的参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| url | str | - | **必需** - Redis 连接 URL |
| max_connections | int | 50 | 连接池中的最大连接数 |
| encoding | str | "utf-8" | 字符串编码 |
| decode_responses | bool | True | 自动解码响应为字符串 |
| socket_connect_timeout | int | 5 | 连接超时（秒） |
| socket_timeout | int | 5 | 套接字超时（秒） |
| health_check_interval | int | 30 | 健康检查间隔（秒） |
| retry_on_timeout | bool | True | 超时时重试 |

### 🔄 向后兼容性

✅ **完全兼容** - 现有代码无需修改

```python
# 这种调用方式仍然有效
await redis_manager.init(url="redis://localhost:6379/0")

# 现在也可以使用明确的参数
await redis_manager.init(
    url="redis://localhost:6379/0",
    max_connections=100,
    socket_connect_timeout=10,
)
```

### 🚫 禁止的模式

❌ **不要** 在 redis 7.x 中使用消息参数：

```python
await redis_manager.client.ping("test")  # ❌ TypeError in redis 7.x
```

✅ **应该** 使用无参数调用：

```python
await redis_manager.client.ping()  # ✅ Works in both 5.x and 7.x
```

### 📁 文件变更

**新增:**
- `src/sengine/db/redis/README.md` - 详细使用文档
- `src/sengine/db/redis/CHANGES.md` - 本变更日志
- `test_redis_redesign.py` - 测试套件

**删除:**
- `src/sengine/db/redis/config.py` - 移除 config 模块
- `src/sengine/db/redis/examples.py` - 合并到 README.md
- `src/sengine/db/redis/DESIGN.md` - 合并到 README.md

**修改:**
- `src/sengine/db/redis/client.py` - 重新设计 init() 方法
- `src/sengine/db/redis/__init__.py` - 更新导出
- `src/sengine/db/__init__.py` - 更新导出

### 🧪 测试

运行测试验证：

```bash
python test_redis_redesign.py
```

所有测试通过：
- ✅ RedisManager 基本功能
- ✅ 完整参数初始化
- ✅ 最小参数初始化
- ✅ 局部参数初始化
- ✅ 连接失败处理
- ✅ 双初始化保护

### 📚 相关文档

- `/resource/plans/db/configuration_analysis.md` - 原始问题分析
- `/resource/plans/db/summary.md` - 执行摘要
- `src/sengine/db/redis/README.md` - 完整使用指南

---

**注意**: 此变更遵循项目规范，明确在 db 模块中定义所有参数，不引用外部 config 模块。
