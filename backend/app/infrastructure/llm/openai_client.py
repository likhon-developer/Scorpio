"""
OpenAI LLM client implementation
"""

import json
from typing import List, Dict, Any, AsyncGenerator
import openai
from openai import AsyncOpenAI

from app.infrastructure.llm.base_client import LLMClientInterface
from app.core.config import settings


class OpenAIClient(LLMClientInterface):
    """OpenAI LLM client"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview"

    async def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        if not settings.OPENAI_API_KEY:
            return False

        try:
            await self.client.models.list()
            return True
        except Exception:
            return False

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from OpenAI"""

        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            if msg["role"] == "system":
                openai_messages.append({"role": "system", "content": msg["content"]})
            elif msg["role"] == "user":
                openai_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                openai_messages.append({"role": "assistant", "content": msg["content"]})

        # Prepare tools for OpenAI
        openai_tools = None
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"]
                    }
                })

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                tools=openai_tools,
                tool_choice="auto" if openai_tools else None,
                stream=True,
                temperature=0.7,
                max_tokens=4000
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta

                if delta.content:
                    yield {
                        "type": "token",
                        "data": delta.content
                    }

                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        if tool_call.function:
                            yield {
                                "type": "tool_call",
                                "data": {
                                    "id": tool_call.id,
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments
                                }
                            }

                if chunk.choices[0].finish_reason:
                    yield {
                        "type": "done",
                        "data": chunk.choices[0].finish_reason
                    }

        except Exception as e:
            yield {
                "type": "error",
                "data": str(e)
            }

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Non-streaming chat completion"""

        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            if msg["role"] == "system":
                openai_messages.append({"role": "system", "content": msg["content"]})
            elif msg["role"] == "user":
                openai_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                openai_messages.append({"role": "assistant", "content": msg["content"]})

        # Prepare tools for OpenAI
        openai_tools = None
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"]
                    }
                })

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=openai_tools,
            tool_choice="auto" if openai_tools else None,
            temperature=0.7,
            max_tokens=4000
        )

        return {
            "content": response.choices[0].message.content,
            "tool_calls": response.choices[0].message.tool_calls,
            "finish_reason": response.choices[0].finish_reason
        }
