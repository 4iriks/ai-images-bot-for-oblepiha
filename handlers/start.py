from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from db.models import ensure_user, get_user
from keyboards.inline import subscription_kb, main_menu_kb
from utils.subscription import check_subscription

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await ensure_user(user.id, user.username, user.full_name)

    if not await check_subscription(message.bot, user.id):
        await message.answer(
            "Для использования бота необходимо подписаться на канал:",
            reply_markup=subscription_kb(),
        )
        return

    await message.answer(
        "Добро пожаловать! Выберите действие:",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        await callback.answer("Вы ещё не подписались на канал!", show_alert=True)
        return

    await callback.message.edit_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=main_menu_kb(),
    )
