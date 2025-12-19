"""Demo script for vLLM OpenAI client

This script demonstrates how to initialize and use a vLLM OpenAI-compatible
client through the LLMManager for text generation tasks.
"""
import os
import sys

sys.path.insert(0, '/data/home/solgeo/projects/reasoning-acting/src')
import asyncio

from react.llm import VllmOpenaiConfig, llm_manager

config = VllmOpenaiConfig(
    provider="vllm_openai",
    model="Text_LLM",
    api_key="dummy_key",
    base_url="http://10.1.0.4:8001",
    temperature=0.1,
    max_tokens=2048,
    timeout=60.0,
    max_retries=3,
    stream=True,
    reasoning=False,
)


async def main() -> None:
    """Main async function to demonstrate vLLM client usage"""
    client = llm_manager.create("vllm_text", config)
    messages = [
        {
            "role": "user",
            "content": "say hello to me"
        }
    ]

    print("non stream request")
    print("=" * 60)
    response = await client.chat_completion(
        messages,
        stream=False,
        enable_thinking=False,
    )

    print(f"Content: {response.content}")
    print(f"Model: {response.__dict__}")

    print("\n" + "=" * 60)
    print(f"[reasoning]stream request")
    stream_response = await client.chat_completion(
        messages,
        stream=True,
        enable_thinking=True,
    )

    async for chunk in stream_response:
        if chunk.delta:
            print(chunk.delta, end="", flush=True)

    print("\n" + "=" * 60)
    print(f"[non-reasoning]stream request")
    stream_response = await client.chat_completion(
        messages,
        stream=True,
        enable_thinking=False,
    )

    async for chunk in stream_response:
        if chunk.delta:
            print(chunk.delta, end="", flush=True)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
