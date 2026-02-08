from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from config import settings
from db.models import (
    get_total_users,
    get_total_generations,
    get_today_generations,
    get_all_keys,
    add_api_key,
    get_keys_usage_percent,
)
from keyboards.inline import admin_menu_kb, back_to_menu_kb

router = Router()


class AdminStates(StatesGroup):
    waiting_for_key = State()


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

    text = (
        "📊 Аналитика:\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🖼 Всего генераций: {total_gens}\n"
        f"📅 Генераций сегодня: {today_gens}\n"
    )
    await callback.message.edit_text(text, reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_keys")
async def admin_keys(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    keys = await get_all_keys()
    if not keys:
        await callback.message.edit_text(
            "🔑 Нет API ключей.\nДобавьте через «➕ Добавить ключ».",
            reply_markup=admin_menu_kb(),
        )
        return

    lines = ["🔑 API ключи:\n"]
    for k in keys:
        status = "✅" if k["is_active"] else "❌"
        pct = (k["usage_count"] / k["usage_limit"] * 100) if k["usage_limit"] > 0 else 0
        masked = k["key"][:8] + "..."
        lines.append(
            f"{status} {masked} — {k['usage_count']}/{k['usage_limit']} ({pct:.0f}%)"
        )

    await callback.message.edit_text("\n".join(lines), reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_add_key")
async def admin_add_key_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_for_key)
    await callback.message.edit_text(
        "Отправьте новый API ключ Pollinations:",
        reply_markup=back_to_menu_kb(),
    )


@router.message(AdminStates.waiting_for_key)
async def admin_add_key_process(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    key = message.text.strip()
    if not key:
        await message.answer("Пожалуйста, отправьте текст ключа.")
        return

    await add_api_key(key)
    await state.clear()
    await message.answer(
        f"✅ Ключ {key[:8]}... добавлен.",
        reply_markup=admin_menu_kb(),
    )


async def notify_admin_keys_usage(bot: Bot):
    """Call this periodically or after generation to check key usage."""
    pct = await get_keys_usage_percent()
    if pct > 80:
        try:
            await bot.send_message(
                settings.admin_id,
                f"⚠️ Внимание! Средняя загрузка API ключей: {pct:.0f}%.\n"
                "Рекомендуется добавить новые ключи.",
            )
        except Exception:
            pass
