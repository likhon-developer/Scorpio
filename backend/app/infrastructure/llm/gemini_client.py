"""
Google Gemini LLM client implementation
"""

import json
from typing import List, Dict, Any, AsyncGenerator
import google.generativeai as genai

from app.infrastructure.llm.base_client import LLMClientInterface
from app.core.config import settings


class GeminiClient(LLMClientInterface):
    """Google Gemini LLM client"""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    async def is_available(self) -> bool:
        """Check if Gemini service is available"""
        return bool(settings.GEMINI_API_KEY)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from Gemini"""

        try:
            # Convert messages to Gemini format
            gemini_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    # Gemini handles system messages differently
                    gemini_messages.append({"role": "user", "parts": [msg["content"]]})
                    gemini_messages.append({"role": "model", "parts": ["Understood."]})
                elif msg["role"] == "user":
                    gemini_messages.append({"role": "user", "parts": [msg["content"]]})
                elif msg["role"] == "assistant":
                    gemini_messages.append({"role": "model", "parts": [msg["content"]]})

            # Start chat session
            chat = self.model.start_chat(history=gemini_messages[:-1] if gemini_messages else [])

            # Send last message and stream response
            response = await chat.send_message_async(
                gemini_messages[-1]["parts"][0] if gemini_messages else "",
                stream=True
            )

            async for chunk in response:
                if chunk.text:
                    yield {
                        "type": "token",
                        "data": chunk.text
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

        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            if msg["role"] == "system":
                gemini_messages.append({"role": "user", "parts": [msg["content"]]})
                gemini_messages.append({"role": "model", "parts": ["Understood."]})
            elif msg["role"] == "user":
                gemini_messages.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg["content"]]})

        chat = self.model.start_chat(history=gemini_messages[:-1] if gemini_messages else [])
        response = await chat.send_message_async(
            gemini_messages[-1]["parts"][0] if gemini_messages else ""
        )

        return {
            "content": response.text,
            "tool_calls": None,  # Not implemented yet
            "finish_reason": "stop"
        }
