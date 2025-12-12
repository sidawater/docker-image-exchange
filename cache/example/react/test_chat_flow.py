#!/usr/bin/env python3
"""
测试chat对话流程和消息写入功能
"""
import sys
import os
sys.path.insert(0, '/data/home/solgeo/projects/chat-service/src/')

import requests
import json
import time
from init.msg import MessageClient
from init.msg.models import QaSearchParams


def test_simple_chat():
    """执行简单的chat对话"""
    print("=" * 60)
    print("测试1: 执行简单chat对话")
    print("=" * 60)

    url = "http://localhost:8686/knowledge/chat-service/chat/completions"
    params = {
        "message": "简单测试：你好",
        "session_id": "test_session_simple",
        "react_instance_code": "default"
    }

    try:
        with requests.post(
            url,
            params=params,
            stream=True,
            timeout=30
        ) as response:
            response.raise_for_status()

            content_received = False
            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode('utf-8')
                if 'data: {"type": "content"' in line:
                    content_received = True
                    print(f"收到content数据: {line[:100]}...")

            if content_received:
                print("✅ 简单chat对话成功")
                return True
            else:
                print("❌ 简单chat对话失败：未收到content数据")
                return False
    except Exception as e:
        print(f"❌ 简单chat对话出错: {e}")
        return False


def test_error_scenario():
    """测试错误场景下的消息写入"""
    print("\n" + "=" * 60)
    print("测试2: 验证错误场景下的消息写入")
    print("=" * 60)

    url = "http://localhost:8686/knowledge/chat-service/chat/completions"
    params = {
        "message": "测试错误：故意发送一个会导致错误的请求",
        "session_id": "test_session_error",
        "react_instance_code": "invalid_code"  # 使用无效的code
    }

    try:
        response = requests.post(url, params=params, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}")
        print("✅ 错误场景测试完成")
        return True
    except Exception as e:
        print(f"✅ 错误场景测试完成（捕获异常）: {e}")
        return True


def verify_messages():
    """验证消息是否写入msg服务"""
    print("\n" + "=" * 60)
    print("测试3: 验证消息写入msg服务")
    print("=" * 60)

    client = MessageClient(
        base_url="http://10.194.203.138/knowledge/message-service",
        api_token="test_token_12345"
    )

    test_sessions = ["test_session_simple", "test_session_error"]

    for session_prefix in test_sessions:
        print(f"\n--- 检查会话: {session_prefix} ---")
        try:
            sessions = client.sessions.list(user_id=session_prefix, offset=0, limit=10)

            if not sessions:
                print(f"❌ 未找到会话 {session_prefix}")
                continue

            session = sessions[0]
            session_id = session.get('id')
            print(f"✅ 找到会话: {session_id}")

            search_params = QaSearchParams(session_id=session_id, offset=0, limit=20)
            items = client.qa.search(search_params)

            print(f"找到 {len(items)} 条 QA 记录")

            for item in items:
                qa_id = item.get('id')
                question = item.get('question', {}).get('content', '')
                answer = item.get('answer', {}).get('content', '')
                create_time = item.get('create_time')

                print(f"  QA ID: {qa_id}")
                print(f"  问题: {question[:50]}...")
                print(f"  答案长度: {len(answer)} 字符")
                print(f"  创建时间: {create_time}")

                if question and not answer:
                    print("  ⚠️  问题已写入，但答案为空")
                elif question and answer:
                    print("  ✅ 问题+答案都已写入")
                elif not question:
                    print("  ❌ 问题未写入")

        except Exception as e:
            print(f"❌ 检查会话 {session_prefix} 时出错: {e}")


def main():
    """主测试流程"""
    print("Chat对话流程测试开始")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 执行测试
    test_simple_chat()
    test_error_scenario()

    # 等待几秒确保消息写入
    time.sleep(3)

    # 验证消息写入
    verify_messages()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
