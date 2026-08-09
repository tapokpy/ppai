from anthropic import AsyncAnthropic

from app.config import settings

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)


async def generate(prompt: str, system: str | None = None) -> str:
    message = await _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
