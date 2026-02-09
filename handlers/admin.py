import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import settings
from db.models import (
    get_total_users, get_total_generations, get_today_generations,
    get_top_prompters, get_top_prompters_today, get_new_users_today,
    get_most_popular_model, get_avg_prompts_per_user, MODELS,
)
from keyboards.inline import admin_menu_kb

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Админ-панель:", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_analytics")
async def admin_analytics(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    # Собираем статистику
    total_users = await get_total_users()
    new_users_today = await get_new_users_today()
    total_gens = await get_total_generations()
    today_gens = await get_today_generations()
    avg_prompts = await get_avg_prompts_per_user()
    popular_model = await get_most_popular_model()
    top_all_time = await get_top_prompters(7)
    top_today = await get_top_prompters_today(7)

    text = (
        "📊 <b>Аналитика бота</b>\n"
        "━━━━━━━━━━━━━━━\n\n"
        "👥 <b>Пользователи:</b>\n"
        f"├ Всего: <code>{total_users}</code>\n"
        f"└ Новых сегодня: <code>{new_users_today}</code>\n\n"
        "🎨 <b>Генерации:</b>\n"
        f"├ Всего: <code>{total_gens}</code>\n"
        f"├ Сегодня: <code>{today_gens}</code>\n"
        f"└ Среднее на юзера: <code>{avg_prompts:.1f}</code>\n\n"
    )

    if popular_model:
        model_id, usage_count = popular_model
        model_info = MODELS.get(model_id, {"name": model_id, "emoji": "🎨"})
        text += (
            f"🔥 <b>Популярная модель:</b>\n"
            f"{model_info['emoji']} {model_info['name']} — <code>{usage_count}</code> использований\n\n"
        )

    if top_today:
        text += "🏆 <b>Топ-7 сегодня:</b>\n"
        for i, u in enumerate(top_today, 1):
            name = u.get("username") or u.get("full_name") or f"ID{u['user_id']}"
            if u.get("username"):
                name = f"@{name}"
            text += f"  {i}. {name} — <code>{u['gen_count']}</code> ген.\n"
        text += "\n"

    if top_all_time:
        text += "🎖 <b>Топ-7 за все время:</b>\n"
        for i, u in enumerate(top_all_time, 1):
            name = u.get("username") or u.get("full_name") or f"ID{u['user_id']}"
            if u.get("username"):
                name = f"@{name}"
            text += f"  {i}. {name} — <code>{u['gen_count']}</code> ген.\n"

    await callback.message.edit_text(text, reply_markup=admin_menu_kb())
