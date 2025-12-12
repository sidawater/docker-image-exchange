"""
Verify chat message was written to message-service
"""
import sys
import os
sys.path.insert(0, '/data/home/solgeo/projects/chat-service/src/')

from init.msg import MessageClient
from init.msg.models import QaSearchParams

def main():
    client = MessageClient(
        base_url="http://10.194.203.138/knowledge/message-service",
        api_token="test_token_12345"
    )

    sessions = client.sessions.list(user_id="my_session_123", offset=0, limit=10)

    if not sessions:
        print("❌ 未找到会话 my_session_123")
        return

    for session in sessions:
        session_id = session.get('id')
        print(f"=== 会话信息 ===")
        print(f"会话ID: {session_id}")
        print(f"用户ID: {session.get('user_id')}")
        print(f"创建时间: {session.get('create_time')}")

        search_params = QaSearchParams(session_id=session_id, offset=0, limit=20)
        items = client.qa.search(search_params)

        print(f"\n=== QA 记录 ===")
        print(f"找到 {len(items)} 条 QA 记录\n")

        for item in items:
            print(f"QA ID: {item.get('id')}")
            print(f"QA Key: {item.get('qa_key')}")
            print(f"问题: {item.get('question', {}).get('content', '')}")
            print(f"答案: {item.get('answer', {}).get('content', '')[:200]}")
            print(f"创建时间: {item.get('create_time')}")
            print("---")

if __name__ == '__main__':
    main()
