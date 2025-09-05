"""
Base LLM client interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator


class LLMClientInterface(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response"""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Non-streaming chat completion"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the LLM service is available"""
        pass
