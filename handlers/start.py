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
    existing_user = await get_user(user.id)
    await ensure_user(user.id, user.username, user.full_name)

    if not await check_subscription(message.bot, user.id):
        await message.answer(
            "🎨 <b>Облепиха Images AI</b>\n\n"
            "Удобный и бесплатный сервис для генерации картинок искусственным интеллектом.\n\n"
            "Сделано с душой, при поддержке команды "
            '<a href="https://t.me/oblepiha_vpn_bot">Облепиха VPN</a> 🧡\n\n'
            "━━━━━━━━━━━━━━━\n\n"
            "📋 <b>Чтобы пользоваться сервисом, необходимо подписаться на канал и запустить бота:</b>",
            reply_markup=subscription_kb(),
        )
        return

    # Если пользователь уже существовал и подписан - приветствие
    if existing_user:
        await message.answer(
            "Приятного пользования сервисом Облепиха images AI 🧡\n\n"
            "💡 Чтобы сгенерировать свою первую картинку - опиши ее",
            reply_markup=main_menu_kb(),
        )
    else:
        # Новый пользователь, только что подписался
        await message.answer(
            "🎉 <b>Спасибо за поддержку, приятного пользования!</b> 🧡\n\n"
            "💡 Чтобы сгенерировать свою первую картинку - опиши ее\n\n"
            "Выберите действие:",
            reply_markup=main_menu_kb(),
        )


@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery):
    if not await check_subscription(callback.bot, callback.from_user.id):
        await callback.answer("❌ Вы ещё не подписались на канал и не запустили бота!", show_alert=True)
        return

    await callback.message.edit_text(
        "🎉 <b>Спасибо за поддержку, приятного пользования!</b> 🧡\n\n"
        "Выберите действие:",
        reply_markup=main_menu_kb(),
    )
