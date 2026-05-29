import anthropic
from config import API_KEY
from collections.abc import AsyncIterable


client = anthropic.AsyncAnthropic(
    api_key=API_KEY
)

async def get_ai_response(messages: list[dict]) -> AsyncIterable[str]:

    async with client.messages.stream(
        model="claude-opus-4-5-20251101",
        max_tokens=1024,
        messages=messages
    ) as stream:
        async for text in stream.text_stream:
            yield text 



