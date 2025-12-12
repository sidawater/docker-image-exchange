import requests


url = "http://localhost:8686/knowledge/chat-service/chat/completions"
# query = 'what should I do with my server since it's becoming slow'
query = 'say hi to me'
params = {
    "message": query,
    "session_id": "my_session_123",
    "react_instance_code": "default"
}


def run():
    """
    运行chat接口示例

    使用POST方法调用chat接口，支持SSE流式响应
    """
    with requests.post(
            url,
            params=params,
            stream=True,
            timeout=60
        ) as response:
        
        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8')
            print(line)


if __name__ == '__main__':
    run()
