from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.models import (
    get_user, set_clarification, set_user_model,
    get_user_model, get_model_usage_today, MODELS,
)
from keyboards.inline import settings_kb, models_kb

router = Router()


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    enabled = bool(user["clarification_enabled"]) if user else True
    model = await get_user_model(callback.from_user.id)
    try:
        await callback.message.edit_text(
            "⚙️ <b>Настройки</b>",
            reply_markup=settings_kb(enabled, model),
        )
    except Exception:
        await callback.message.answer(
            "⚙️ <b>Настройки</b>",
            reply_markup=settings_kb(enabled, model),
        )


@router.callback_query(F.data == "toggle_clarification")
async def toggle_clarification(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    current = bool(user["clarification_enabled"]) if user else True
    new_value = not current
    await set_clarification(callback.from_user.id, new_value)
    model = await get_user_model(callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_kb(new_value, model),
    )


@router.callback_query(F.data == "choose_model")
async def choose_model(callback: CallbackQuery):
    user_id = callback.from_user.id
    current = await get_user_model(user_id)
    usage_map = {}
    for model_id in MODELS:
        usage_map[model_id] = await get_model_usage_today(user_id, model_id)

    await callback.message.edit_text(
        "🎨 <b>Выберите модель генерации</b>\n\n"
        "В скобках — оставшиеся генерации на сегодня.",
        reply_markup=models_kb(current, usage_map),
    )


@router.callback_query(F.data.startswith("set_model:"))
async def set_model(callback: CallbackQuery):
    model_id = callback.data.split(":", 1)[1]
    if model_id not in MODELS:
        await callback.answer("Неизвестная модель")
        return

    user_id = callback.from_user.id
    info = MODELS[model_id]

    # Check if limit reached
    if info["limit"] > 0:
        used = await get_model_usage_today(user_id, model_id)
        if used >= info["limit"]:
            await callback.answer(
                f"Лимит {info['name']} исчерпан на сегодня ({info['limit']}/{info['limit']})",
                show_alert=True,
            )
            return

    await set_user_model(user_id, model_id)
    await callback.answer(f"{info['emoji']} {info['name']} выбрана!")

    # Refresh the model list
    current = model_id
    usage_map = {}
    for mid in MODELS:
        usage_map[mid] = await get_model_usage_today(user_id, mid)

    await callback.message.edit_text(
        "🎨 <b>Выберите модель генерации</b>\n\n"
        "В скобках — оставшиеся генерации на сегодня.",
        reply_markup=models_kb(current, usage_map),
    )
