import asyncio
import logging

import httpx
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message

from bot.config import settings
from bot.handlers.rules import router as rules_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()
dp.include_router(rules_router)


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Здравствуйте! Я ассистент «ПридПром». Напишите вопрос по расчётам "
        "или технической документации."
    )


@dp.message(StateFilter(None))
async def handle_message(message: Message) -> None:
    async with httpx.AsyncClient(base_url=settings.backend_url, timeout=120) as client:
        response = await client.post(
            "/chat/query",
            json={"query": message.text, "user_id": str(message.from_user.id)},
        )
        response.raise_for_status()
        data = response.json()

    await message.answer(data["answer"])


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
