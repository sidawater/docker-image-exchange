"""
README - 消息服务客户端

消息服务API的Python客户端实现。
"""

# 消息服务客户端

消息服务API的Python客户端，提供会话管理、QA记录管理和附件管理功能。

## 安装依赖

```bash
pip install httpx pydantic
```

## 快速开始

### 初始化客户端

```python
from init.msg import MessageClient

client = MessageClient(
    base_url="http://localhost:8000",
    api_token="your_api_token_here"
)

# 使用上下文管理器（推荐）
with MessageClient(
    base_url="http://localhost:8000",
    api_token="your_api_token_here"
) as client:
    # 使用客户端
    pass
```

### 会话管理

```python
from init.msg.models import SessionCreateRequest, SessionUpdateRequest

# 创建会话
create_request = SessionCreateRequest(
    user_id="user123",
    title="My Session",
    metadata={"topic": "general"}
)
session = client.sessions.create(create_request)

# 获取会话
session_id = session["id"]
retrieved = client.sessions.get(session_id)

# 列出用户会话
sessions = client.sessions.list(
    user_id="user123",
    offset=0,
    limit=10
)

# 更新会话
update_request = SessionUpdateRequest(
    title="Updated Title"
)
updated = client.sessions.update(session_id, update_request)

# 删除会话
client.sessions.delete(session_id)
```

### QA记录管理

```python
from init.msg.models import QaCreateRequest, QaMessageContent, QaUpdateRequest

# 创建QA记录
create_request = QaCreateRequest(
    session_id="session123",
    qa_key="qa_001",
    question=QaMessageContent(
        content="What is Python?",
        attaches=[]
    ),
    answer=QaMessageContent(
        content="Python is a programming language.",
        attaches=[]
    )
)
qa_record = client.qa.create(create_request)

# 获取QA记录
qa_id = qa_record["id"]
retrieved = client.qa.get(qa_id)

# 搜索QA记录
results = client.qa.search(
    session_id="session123",
    offset=0,
    limit=10
)

# 获取会话的所有QA记录
qa_list = client.qa.get_by_session(
    session_id="session123",
    limit=20
)

# 更新QA记录
update_request = QaUpdateRequest(
    answer=QaMessageContent(
        content="Updated answer",
        attaches=[]
    )
)
updated = client.qa.update(qa_id, update_request)
```

### 附件管理

```python
# 上传附件
with open("document.pdf", "rb") as f:
    file_data = f.read()

attachment = client.attachments.upload(
    file_data=file_data,
    qa_id="qa123",
    attach_key=1,
    file_type="application/pdf",
    filename="document.pdf"
)

# 获取附件信息
attachment_id = attachment["id"]
info = client.attachments.get(attachment_id)

# 获取下载URL
url_info = client.attachments.get_download_url(
    attachment_id,
    expires_in=3600
)

# 下载附件
content = client.attachments.download(attachment_id)

# 删除附件
client.attachments.delete(attachment_id)
```

## API参考

### MessageClient

主客户端类，整合所有功能模块。

**属性：**
- `sessions`: 会话管理客户端
- `qa`: QA记录管理客户端
- `attachments`: 附件管理客户端

**方法：**
- `health_check()`: 健康检查
- `get_swagger_docs()`: 获取API文档
- `close()`: 关闭客户端

### SessionClient

会话管理客户端。

**方法：**
- `create(request)`: 创建会话
- `get(session_id)`: 获取会话详情
- `list(user_id, offset, limit, active_only)`: 列出用户会话
- `update(session_id, request)`: 更新会话
- `delete(session_id)`: 删除会话

### QaClient

QA记录管理客户端。

**方法：**
- `create(request)`: 创建QA记录
- `get(qa_id)`: 获取QA记录详情
- `update(qa_id, request)`: 更新QA记录
- `search(params)`: 搜索QA记录
- `get_by_session(session_id, limit, offset)`: 获取会话的所有QA记录

### AttachmentClient

附件管理客户端。

**方法：**
- `upload(file_data, qa_id, attach_key, file_type, filename)`: 上传附件
- `get(attachment_id)`: 获取附件信息
- `get_download_url(attachment_id, expires_in)`: 获取下载URL
- `download(attachment_id)`: 下载附件内容
- `delete(attachment_id)`: 删除附件

## 异常处理

客户端定义了以下异常类型：

- `MessageServiceError`: 基础异常
- `ValidationError`: 验证错误（HTTP 422）
- `NotFoundError`: 资源未找到（HTTP 404）
- `AuthenticationError`: 认证错误（HTTP 401）
- `ServerError`: 服务器错误（HTTP 5xx）

```python
from init.msg.exceptions import ValidationError, NotFoundError

try:
    session = client.sessions.get("invalid_id")
except NotFoundError:
    print("Session not found")
except ValidationError as e:
    print(f"Validation error: {e}")
```

## 配置选项

### 超时设置

```python
client = MessageClient(
    base_url="http://localhost:8000",
    api_token="your_token",
    timeout=60  # 60秒超时
)
```

### 临时下载URL

附件下载功能通过获取临时URL实现：

```python
url_info = client.attachments.get_download_url(
    attachment_id,
    expires_in=3600  # URL有效期3600秒
)
```

## 最佳实践

1. **使用上下文管理器**：确保资源正确释放
2. **异常处理**：始终捕获和处理可能的异常
3. **资源管理**：及时关闭客户端或使用上下文管理器
4. **参数验证**：使用提供的模型类进行参数验证
5. **分页处理**：对于大量数据，使用分页参数

## 许可证

本项目遵循项目许可证。
