from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.models import get_user, set_clarification
from keyboards.inline import settings_kb

router = Router()


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    enabled = bool(user["clarification_enabled"]) if user else True
    await callback.message.edit_text(
        "Настройки:",
        reply_markup=settings_kb(enabled),
    )


@router.callback_query(F.data == "toggle_clarification")
async def toggle_clarification(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    current = bool(user["clarification_enabled"]) if user else True
    new_value = not current
    await set_clarification(callback.from_user.id, new_value)
    await callback.message.edit_text(
        "Настройки:",
        reply_markup=settings_kb(new_value),
    )
