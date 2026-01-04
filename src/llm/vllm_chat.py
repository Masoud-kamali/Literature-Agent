"""vLLM OpenAI-compatible chat client."""

from typing import List, Optional

from loguru import logger
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings


class VLLMChatClient:
    """
    Client for vLLM OpenAI-compatible API.

    Uses the OpenAI Python client pointed at a local vLLM server.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialise vLLM client.

        Args:
            base_url: vLLM server endpoint (defaults to config)
            api_key: Dummy API key (defaults to config)
            model_name: Model name as configured in vLLM (defaults to config)
            temperature: Sampling temperature (defaults to config)
            max_tokens: Max tokens to generate (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
        """
        self.base_url = base_url or settings.vllm_base_url
        self.api_key = api_key or settings.vllm_api_key
        self.model_name = model_name or settings.vllm_model_name
        self.temperature = temperature if temperature is not None else settings.vllm_temperature
        self.max_tokens = max_tokens or settings.vllm_max_tokens
        self.timeout = timeout or settings.vllm_timeout

        # Initialise async OpenAI client
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

        logger.info(
            f"Initialised vLLM client: base_url={self.base_url}, model={self.model_name}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, max=30),
    )
    async def chat_completion(
        self,
        messages: List[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override temperature
            max_tokens: Override max_tokens

        Returns:
            Generated text content
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens or self.max_tokens

        logger.debug(f"Chat completion request: {len(messages)} messages, temp={temp}")

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
            )

            content = response.choices[0].message.content
            logger.debug(f"Chat completion response: {len(content)} characters")

            return content

        except Exception as e:
            logger.error(f"vLLM chat completion failed: {e}")
            raise

    async def generate_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate completion with system and user prompts.

        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Override temperature
            max_tokens: Override max_tokens

        Returns:
            Generated text content
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return await self.chat_completion(messages, temperature, max_tokens)
