"""
消息服务客户端使用示例

演示如何使用MessageClient进行各种操作。
"""

from . import MessageClient
from .models import (
    SessionCreateRequest,
    SessionUpdateRequest,
    QaCreateRequest,
    QaMessageContent,
    QaUpdateRequest
)


def example_session_operations():
    """会话操作示例"""
    client = MessageClient(
        base_url="http://localhost:8000",
        api_token="your_api_token_here"
    )

    try:
        create_request = SessionCreateRequest(
            user_id="user123",
            title="My First Session",
            metadata={"topic": "general"}
        )

        session = client.sessions.create(create_request)
        print(f"Created session: {session}")

        session_id = session.get("id")

        retrieved_session = client.sessions.get(session_id)
        print(f"Retrieved session: {retrieved_session}")

        sessions_list = client.sessions.list(
            user_id="user123",
            offset=0,
            limit=10
        )
        print(f"User sessions: {sessions_list}")

        update_request = SessionUpdateRequest(
            title="Updated Session Title"
        )
        updated_session = client.sessions.update(session_id, update_request)
        print(f"Updated session: {updated_session}")

        client.sessions.delete(session_id)
        print("Session deleted")

    finally:
        client.close()


def example_qa_operations():
    """QA记录操作示例"""
    client = MessageClient(
        base_url="http://localhost:8000",
        api_token="your_api_token_here"
    )

    try:
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
        print(f"Created QA record: {qa_record}")

        qa_id = qa_record.get("id")

        retrieved_qa = client.qa.get(qa_id)
        print(f"Retrieved QA: {retrieved_qa}")

        search_results = client.qa.search(
            session_id="session123",
            offset=0,
            limit=10
        )
        print(f"Search results: {search_results}")

        session_qa_list = client.qa.get_by_session(
            session_id="session123",
            limit=20
        )
        print(f"Session QA list: {session_qa_list}")

        update_request = QaUpdateRequest(
            answer=QaMessageContent(
                content="Python is a high-level programming language.",
                attaches=[]
            )
        )
        updated_qa = client.qa.update(qa_id, update_request)
        print(f"Updated QA: {updated_qa}")

    finally:
        client.close()


def example_attachment_operations():
    """附件操作示例"""
    client = MessageClient(
        base_url="http://localhost:8000",
        api_token="your_api_token_here"
    )

    try:
        file_data = b"Test file content"

        attachment = client.attachments.upload(
            file_data=file_data,
            qa_id="qa123",
            attach_key=1,
            file_type="text/plain",
            filename="test.txt"
        )
        print(f"Uploaded attachment: {attachment}")

        attachment_id = attachment.get("id")

        attachment_info = client.attachments.get(attachment_id)
        print(f"Attachment info: {attachment_info}")

        temp_url_info = client.attachments.get_download_url(
            attachment_id,
            expires_in=3600
        )
        print(f"Temporary URL: {temp_url_info}")

        downloaded_content = client.attachments.download(attachment_id)
        print(f"Downloaded content length: {len(downloaded_content)}")

        client.attachments.delete(attachment_id)
        print("Attachment deleted")

    finally:
        client.close()


def example_context_manager():
    """使用上下文管理器的示例"""
    with MessageClient(
        base_url="http://localhost:8000",
        api_token="your_api_token_here"
    ) as client:
        health = client.health_check()
        print(f"Service health: {health}")

        sessions = client.sessions.list(
            user_id="user123",
            offset=0
        )
        print(f"Sessions: {sessions}")


if __name__ == "__main__":
    print("Running examples...")
    print("\n=== Session Operations ===")
    example_session_operations()

    print("\n=== QA Operations ===")
    example_qa_operations()

    print("\n=== Attachment Operations ===")
    example_attachment_operations()

    print("\n=== Context Manager Example ===")
    example_context_manager()
