from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BufferedInputFile

from db.models import get_user, add_generation
from keyboards.inline import cancel_kb, main_menu_kb
from services.gemini import GeminiService
from services.logger import log_generation
from services.pollinations import PollinationsService
from states.generation import GenerationStates

router = Router()


@router.callback_query(F.data == "generate")
async def start_generation(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GenerationStates.waiting_for_prompt)
    await callback.message.edit_text(
        "Опишите, какое изображение вы хотите сгенерировать:",
        reply_markup=cancel_kb(),
    )


@router.callback_query(F.data == "cancel_generation")
async def cancel_generation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Генерация отменена. Выберите действие:",
        reply_markup=main_menu_kb(),
    )


@router.message(GenerationStates.waiting_for_prompt)
async def process_prompt(
    message: Message,
    state: FSMContext,
    gemini_service: GeminiService,
    pollinations_service: PollinationsService,
):
    prompt = message.text
    if not prompt:
        await message.answer("Пожалуйста, отправьте текстовое описание.")
        return

    await state.update_data(original_prompt=prompt)
    user = await get_user(message.from_user.id)
    clarification_enabled = bool(user["clarification_enabled"]) if user else True

    if clarification_enabled:
        wait_msg = await message.answer("🤔 Готовлю уточняющие вопросы...")
        try:
            questions = await gemini_service.generate_clarifying_questions(prompt)
            await state.update_data(questions=questions)
            await state.set_state(GenerationStates.waiting_for_clarification)
            await wait_msg.edit_text(
                f"Уточняющие вопросы:\n\n{questions}\n\n"
                "Ответьте на вопросы одним сообщением или нажмите «Пропустить»:",
                reply_markup=cancel_kb(),
            )
        except Exception:
            # Fallback: generate without clarification
            await wait_msg.edit_text("⚠️ Не удалось получить вопросы, генерирую напрямую...")
            await _do_generation(message, state, pollinations_service, prompt, prompt)
    else:
        await _do_generation(message, state, pollinations_service, prompt, prompt)


@router.message(GenerationStates.waiting_for_clarification)
async def process_clarification(
    message: Message,
    state: FSMContext,
    gemini_service: GeminiService,
    pollinations_service: PollinationsService,
):
    answers = message.text
    if not answers:
        await message.answer("Пожалуйста, отправьте текстовые ответы.")
        return

    data = await state.get_data()
    original_prompt = data["original_prompt"]

    wait_msg = await message.answer("🎨 Формирую промт и генерирую изображение...")
    try:
        final_prompt = await gemini_service.refine_prompt(original_prompt, answers)
    except Exception:
        final_prompt = original_prompt

    await _do_generation(message, state, pollinations_service, original_prompt, final_prompt, wait_msg)


async def _do_generation(
    message: Message,
    state: FSMContext,
    pollinations: PollinationsService,
    original_prompt: str,
    final_prompt: str,
    status_msg: Message | None = None,
):
    bot: Bot = message.bot  # type: ignore[assignment]

    if status_msg is None:
        status_msg = await message.answer("🎨 Генерирую изображение...")

    image_data = await pollinations.generate_image(final_prompt)
    await state.clear()

    if image_data is None:
        await status_msg.edit_text(
            "😔 Не удалось сгенерировать изображение. Попробуйте позже.",
            reply_markup=main_menu_kb(),
        )
        return

    await add_generation(message.from_user.id, original_prompt, final_prompt)

    photo = BufferedInputFile(image_data, filename="generation.png")
    caption = f"🎨 {original_prompt[:900]}"
    await message.answer_photo(photo=photo, caption=caption, reply_markup=main_menu_kb())

    try:
        await status_msg.delete()
    except Exception:
        pass

    await log_generation(
        bot,
        message.from_user.id,
        message.from_user.username,
        original_prompt,
        final_prompt,
        image_data,
    )
