import httpx
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import settings

router = Router()

# Категории должны совпадать с теми, что используются в cascade_router
# (category в /chat/query) — сейчас есть только "general", остальные
# появятся вместе с калькуляторами (cable_calc, module_calc, ...).
CATEGORIES = ["general"]


class AddRuleStates(StatesGroup):
    choosing_category = State()
    entering_text = State()


def _is_admin(telegram_id: int) -> bool:
    return telegram_id == settings.admin_telegram_id


def _category_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=cat, callback_data=f"add_rule_cat:{cat}")] for cat in CATEGORIES]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("add_rule"))
async def add_rule_start(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer("Команда доступна только администратору.")
        return

    await state.set_state(AddRuleStates.choosing_category)
    await message.answer("Выберите категорию правила:", reply_markup=_category_keyboard())


@router.callback_query(AddRuleStates.choosing_category)
async def add_rule_category_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split(":", 1)[1]
    await state.update_data(category=category)
    await state.set_state(AddRuleStates.entering_text)
    await callback.message.answer(f"Категория: {category}\nВведите текст правила:")
    await callback.answer()


@router.message(AddRuleStates.entering_text)
async def add_rule_text_entered(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    category = data["category"]

    async with httpx.AsyncClient(base_url=settings.backend_url, timeout=30) as client:
        response = await client.post(
            "/business-rules",
            json={
                "category": category,
                "text": message.text,
                "created_by_telegram_id": message.from_user.id,
            },
        )
        response.raise_for_status()

    await state.clear()
    await message.answer("Правило сохранено.")


@router.message(Command("rules"))
async def list_rules(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer("Команда доступна только администратору.")
        return

    async with httpx.AsyncClient(base_url=settings.backend_url, timeout=30) as client:
        response = await client.get("/business-rules", params={"active_only": True})
        response.raise_for_status()
        rules = response.json()

    if not rules:
        await message.answer("Активных правил нет.")
        return

    for rule in rules:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Деактивировать", callback_data=f"deactivate_rule:{rule['id']}")]
            ]
        )
        await message.answer(f"[{rule['category']}] {rule['text']}", reply_markup=keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith("deactivate_rule:"))
async def deactivate_rule(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Недоступно.", show_alert=True)
        return

    rule_id = callback.data.split(":", 1)[1]
    async with httpx.AsyncClient(base_url=settings.backend_url, timeout=30) as client:
        response = await client.patch(f"/business-rules/{rule_id}", params={"is_active": False})
        response.raise_for_status()

    await callback.message.edit_text(callback.message.text + "\n\n[Деактивировано]")
    await callback.answer()
