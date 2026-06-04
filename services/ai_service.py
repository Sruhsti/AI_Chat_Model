from openai import AsyncOpenAI
from config import API_KEY
from collections.abc import AsyncIterable


client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

async def get_ai_response(messages: list[dict]) -> AsyncIterable[str]:
    stream = await client.chat.completions.create(
        model="deepseek/deepseek-v4-pro",
        max_tokens=1024,
        messages=messages,
        stream=True
    )
    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content



