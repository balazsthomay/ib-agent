"""LLM client service using OpenRouter for unified access to multiple providers."""

from typing import AsyncIterator

from openai import AsyncOpenAI

from app.config import settings


class LLMClient:
    """
    Unified LLM client using OpenRouter.

    OpenRouter provides access to models from multiple providers through a single API:
    - Anthropic: anthropic/claude-3.5-sonnet, anthropic/claude-3-opus, etc.
    - OpenAI: openai/gpt-4, openai/gpt-4-turbo, etc.
    - Google: google/gemini-pro, etc.
    - And many more...
    """

    def __init__(self):
        """Initialize OpenRouter client."""
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )

    async def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        stream: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> str | AsyncIterator[str]:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (e.g., 'anthropic/claude-3.5-sonnet', 'openai/gpt-4')
                   Uses default from settings if not specified
            stream: Whether to stream the response
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            **kwargs: Additional OpenRouter parameters

        Returns:
            Complete response text or async iterator of text chunks if streaming
        """
        model = model or settings.default_llm_model

        if stream:
            return self._stream_completion(messages, model, max_tokens, temperature, **kwargs)

        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content

    async def chat_completion_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (defaults to settings.default_llm_model)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            **kwargs: Additional OpenRouter parameters

        Yields:
            Text chunks as they arrive
        """
        model = model or settings.default_llm_model
        async for chunk in self._stream_completion(messages, model, max_tokens, temperature, **kwargs):
            yield chunk

    async def _stream_completion(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int,
        temperature: float,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream completion response."""
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content


# Singleton instance
llm_client = LLMClient()
