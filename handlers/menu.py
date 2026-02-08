from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.inline import main_menu_kb

router = Router()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(
            "Выберите действие:",
            reply_markup=main_menu_kb(),
        )
    except Exception:
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_kb(),
        )
