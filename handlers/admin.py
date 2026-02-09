import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import settings
from db.models import get_total_users, get_total_generations, get_today_generations, get_top_prompters
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

    total_users = await get_total_users()
    total_gens = await get_total_generations()
    today_gens = await get_today_generations()
    top = await get_top_prompters(5)

    text = (
        "📊 Аналитика:\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🖼 Всего генераций: {total_gens}\n"
        f"📅 Генераций сегодня: {today_gens}\n"
    )

    if top:
        text += "\n🏆 Топ промтеров:\n"
        for i, u in enumerate(top, 1):
            name = u["username"] or u["full_name"] or str(u["user_id"])
            text += f"  {i}. {name} — {u['gen_count']} ген.\n"

    await callback.message.edit_text(text, reply_markup=admin_menu_kb())
