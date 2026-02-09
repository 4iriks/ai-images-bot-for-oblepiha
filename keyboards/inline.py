from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import settings
from db.models import MODELS


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


def settings_kb(clarification_enabled: bool, current_model: str) -> InlineKeyboardMarkup:
    status = "ВКЛ ✅" if clarification_enabled else "ВЫКЛ ❌"
    model_info = MODELS.get(current_model, {"name": current_model, "emoji": "🎨"})
    model_label = f"{model_info['emoji']} {model_info['name']}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Уточнение промта: {status}", callback_data="toggle_clarification")],
        [InlineKeyboardButton(text=f"Модель: {model_label}", callback_data="choose_model")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
    ])


def models_kb(current_model: str, usage_map: dict[str, int]) -> InlineKeyboardMarkup:
    buttons = []
    for model_id, info in MODELS.items():
        selected = " ✓" if model_id == current_model else ""
        limit = info["limit"]
        used = usage_map.get(model_id, 0)
        if limit == 0:
            badge = "∞"
        else:
            remaining = max(0, limit - used)
            badge = f"{remaining}/{limit}"
        label = f"{info['emoji']} {info['name']} [{badge}]{selected}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"set_model:{model_id}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_generation")],
    ])


def clarification_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏩ Пропустить", callback_data="skip_clarification")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_generation")],
    ])


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")],
    ])


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Аналитика", callback_data="admin_analytics")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")],
    ])
