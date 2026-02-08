from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import settings


def subscription_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{settings.required_channel.lstrip('@')}")],
    ]
    if settings.required_bot:
        buttons.append(
            [InlineKeyboardButton(text="Запустить бота", url=f"https://t.me/{settings.required_bot.lstrip('@')}")]
        )
    buttons.append(
        [InlineKeyboardButton(text="Проверить подписку ✅", callback_data="check_subscription")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Генерация", callback_data="generate")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
    ])


def settings_kb(clarification_enabled: bool) -> InlineKeyboardMarkup:
    status = "ВКЛ ✅" if clarification_enabled else "ВЫКЛ ❌"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Уточнение промта: {status}", callback_data="toggle_clarification")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_generation")],
    ])


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")],
    ])


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Аналитика", callback_data="admin_analytics")],
        [InlineKeyboardButton(text="🔑 API ключи", callback_data="admin_keys")],
        [InlineKeyboardButton(text="➕ Добавить ключ", callback_data="admin_add_key")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")],
    ])
