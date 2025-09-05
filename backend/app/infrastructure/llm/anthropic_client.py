"""
Anthropic LLM client implementation
"""

import json
from typing import List, Dict, Any, AsyncGenerator
import anthropic

from app.infrastructure.llm.base_client import LLMClientInterface
from app.core.config import settings


class AnthropicClient(LLMClientInterface):
    """Anthropic Claude LLM client"""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-sonnet-20240229"

    async def is_available(self) -> bool:
        """Check if Anthropic service is available"""
        return bool(settings.ANTHROPIC_API_KEY)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from Anthropic"""

        # Convert messages to Anthropic format
        anthropic_messages = []
        system_message = None

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "user":
                anthropic_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                anthropic_messages.append({"role": "assistant", "content": msg["content"]})

        try:
            # Build request parameters
            params = {
                "model": self.model,
                "messages": anthropic_messages,
                "max_tokens": 4000,
                "temperature": 0.7,
                "stream": True
            }

            if system_message:
                params["system"] = system_message

            # Note: Anthropic tool calling would need to be implemented here
            # For now, we'll skip tool support

            async with self.client.messages.stream(**params) as stream:
                async for chunk in stream:
                    if chunk.type == "content_block_delta":
                        if chunk.delta.text:
                            yield {
                                "type": "token",
                                "data": chunk.delta.text
                            }

                yield {
                    "type": "done",
                    "data": "stop"
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

        # Convert messages to Anthropic format
        anthropic_messages = []
        system_message = None

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "user":
                anthropic_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                anthropic_messages.append({"role": "assistant", "content": msg["content"]})

        params = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": 4000,
            "temperature": 0.7
        }

        if system_message:
            params["system"] = system_message

        response = await self.client.messages.create(**params)

        return {
            "content": response.content[0].text if response.content else "",
            "tool_calls": None,  # Not implemented yet
            "finish_reason": "stop"
        }
