#!/usr/bin/env python3
"""
创建默认 ReActInstance 的接口调用脚本

通过 HTTP API 调用创建一个 code='default' 的 ReAct 实例
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8686/knowledge/chat-service"


def create_default_react_instance():
    """
    创建默认的 ReAct 实例
    """

    # API 端点
    url = f"{BASE_URL}/react"

    # 请求数据 - 使用环境变量中的 LLM 配置
    data = {
        # 基本信息
        "name": "默认 ReAct 实例",
        "code": "default",
        "description": "通过 API 自动创建的默认 ReAct 实例",

        # LLM 配置 - 使用 .env 中的配置
        "llm_provider": "openai",
        "llm_model": "Text_LLM",
        "llm_api_key": "dummy_key",
        "llm_base_url": "http://10.1.0.4:8001",
        "llm_temperature": 0.1,
        "llm_max_tokens": 2048,
        "llm_timeout": 60,
        "llm_max_retries": 3,

        # MCP 配置 - 默认禁用
        "mcp_enabled": False,
        "mcp_servers": [],

        # RAG 配置 - 默认启用
        "rag_enabled": True,
        "rag_endpoint": None,
        "rag_api_key": None,
        "rag_top_k": 5,
        "rag_score_threshold": 0.7,

        # 运行配置
        "max_iterations": 10,
        "timeout": 300,
        "enable_streaming": True,

        # 元数据
        "metadata": {
            "created_by": "api_script",
            "purpose": "default_instance_for_chat_testing"
        },
        "tags": ["default", "chat", "api-created"]
    }

    print("=" * 60)
    print("创建默认 ReActInstance")
    print("=" * 60)
    print(f"\nAPI 端点: {url}")
    print(f"实例代码: {data['code']}")
    print(f"实例名称: {data['name']}")

    try:
        # 发送 POST 请求
        print("\n正在发送请求...")
        response = requests.post(url, json=data, timeout=30)

        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n✅ 创建成功！")
            print("\n实例信息:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            # 如果创建成功，尝试激活实例
            instance_id = result.get('id')
            if instance_id:
                print(f"\n{'=' * 60}")
                print(f"尝试激活实例: {instance_id}")
                print(f"{'=' * 60}")

                activate_url = f"{BASE_URL}/react/{instance_id}/activate"
                activate_response = requests.post(activate_url, timeout=30)

                print(f"激活响应状态码: {activate_response.status_code}")

                if activate_response.status_code == 200:
                    activate_result = activate_response.json()
                    print("\n✅ 激活成功！")
                    print("\n激活结果:")
                    print(json.dumps(activate_result, indent=2, ensure_ascii=False))
                else:
                    print(f"\n⚠️ 激活失败，状态码: {activate_response.status_code}")
                    print(f"错误信息: {activate_response.text}")

            return True

        else:
            print(f"\n❌ 创建失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")

            # 尝试解析错误信息
            try:
                error_info = response.json()
                print("\n错误详情:")
                print(json.dumps(error_info, indent=2, ensure_ascii=False))
            except:
                pass

            return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求异常: {e}")
        return False

    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_react_instances():
    """
    列出所有 ReAct 实例
    """

    url = f"{BASE_URL}/react"

    print("\n" + "=" * 60)
    print("查询现有 ReAct 实例")
    print("=" * 60)

    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print(f"\n共找到 {result.get('total', 0)} 个实例")

            if result.get('items'):
                print("\n实例列表:")
                for item in result['items']:
                    print(f"  - ID: {item['id']}, Code: {item['code']}, Name: {item['name']}, Status: {item['status']}, Enabled: {item['is_enabled']}")
        else:
            print(f"查询失败，状态码: {response.status_code}")

    except Exception as e:
        print(f"查询异常: {e}")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("ReAct Instance 创建脚本")
    print("=" * 60)

    # 先列出现有实例
    list_react_instances()

    # 创建默认实例
    success = create_default_react_instance()

    # 再次列出实例
    list_react_instances()

    # 退出
    sys.exit(0 if success else 1)
