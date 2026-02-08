import asyncio

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, BufferedInputFile

from db.models import (
    get_user, add_generation, get_user_model,
    get_model_usage_today, add_model_usage, MODELS,
)
from keyboards.inline import cancel_kb, clarification_kb, main_menu_kb
from services.gemini import GeminiService
from services.logger import log_generation
from services.pollinations import PollinationsService
from states.generation import GenerationStates

router = Router()


@router.callback_query(F.data == "generate")
async def start_generation(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GenerationStates.waiting_for_prompt)
    try:
        await callback.message.edit_text(
            "Отправьте описание или фото (можно с подписью):",
            reply_markup=cancel_kb(),
        )
    except Exception:
        await callback.message.answer(
            "Отправьте описание или фото (можно с подписью):",
            reply_markup=cancel_kb(),
        )


@router.callback_query(F.data == "cancel_generation")
async def cancel_generation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(
            "Генерация отменена. Выберите действие:",
            reply_markup=main_menu_kb(),
        )
    except Exception:
        await callback.message.answer(
            "Генерация отменена. Выберите действие:",
            reply_markup=main_menu_kb(),
        )


@router.callback_query(F.data == "skip_clarification")
async def skip_clarification(
    callback: CallbackQuery,
    state: FSMContext,
    gemini_service: GeminiService,
    pollinations_service: PollinationsService,
):
    data = await state.get_data()
    prompt = data.get("original_prompt", "")
    if not prompt:
        await state.clear()
        await callback.message.answer("Выберите действие:", reply_markup=main_menu_kb())
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    wait_msg = await callback.message.answer("🎨 Формирую промт и генерирую...")
    try:
        final_prompt = await gemini_service.enhance_prompt(prompt)
    except Exception:
        final_prompt = prompt

    await _do_generation(callback.message, state, pollinations_service, prompt, final_prompt, wait_msg, source_chat=callback.message, user_id=callback.from_user.id, username=callback.from_user.username)


@router.message(GenerationStates.waiting_for_prompt, F.photo)
async def process_photo_prompt(
    message: Message,
    state: FSMContext,
    gemini_service: GeminiService,
    pollinations_service: PollinationsService,
):
    caption = message.caption or ""
    bot: Bot = message.bot  # type: ignore[assignment]

    wait_msg = await message.answer("🎨 Анализирую изображение и формирую промт...")

    photo = message.photo[-1]
    file = await bot.download(photo)
    image_bytes = file.read()

    try:
        final_prompt = await gemini_service.enhance_prompt_with_image(image_bytes, caption)
    except Exception:
        if caption:
            final_prompt = caption
        else:
            await wait_msg.edit_text("😔 Не удалось проанализировать изображение.", reply_markup=main_menu_kb())
            await state.clear()
            return

    await _do_generation(message, state, pollinations_service, caption or "image-based", final_prompt, wait_msg)


@router.message(GenerationStates.waiting_for_prompt)
async def process_prompt(
    message: Message,
    state: FSMContext,
    gemini_service: GeminiService,
    pollinations_service: PollinationsService,
):
    prompt = message.text
    if not prompt:
        await message.answer("Пожалуйста, отправьте текстовое описание или фото.")
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

            text = (
                f"<b>Ваш запрос:</b> <i>{prompt}</i>\n\n"
                f"<b>Уточняющие вопросы:</b>\n\n{questions}\n\n"
                "Ответьте одним сообщением или нажмите <b>«Пропустить»</b>:"
            )
            await wait_msg.edit_text(text, reply_markup=clarification_kb())
        except Exception:
            await wait_msg.edit_text("⚠️ Не удалось получить вопросы, формирую промт...")
            try:
                final_prompt = await gemini_service.enhance_prompt(prompt)
            except Exception:
                final_prompt = prompt
            await _do_generation(message, state, pollinations_service, prompt, final_prompt)
    else:
        wait_msg = await message.answer("🎨 Формирую промт и генерирую...")
        try:
            final_prompt = await gemini_service.enhance_prompt(prompt)
        except Exception:
            final_prompt = prompt
        await _do_generation(message, state, pollinations_service, prompt, final_prompt, wait_msg)


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

    wait_msg = await message.answer("🎨 Формирую промт и генерирую...")
    try:
        final_prompt = await gemini_service.refine_prompt(original_prompt, answers)
    except Exception:
        final_prompt = original_prompt

    await _do_generation(message, state, pollinations_service, original_prompt, final_prompt, wait_msg)


# Catch any photo when no state is set — treat as new generation
@router.message(F.photo)
async def auto_generate_photo(
    message: Message,
    state: FSMContext,
    gemini_service: GeminiService,
    pollinations_service: PollinationsService,
):
    await state.set_state(GenerationStates.waiting_for_prompt)
    await process_photo_prompt(message, state, gemini_service, pollinations_service)


# Catch any text when no state is set — treat as new generation prompt
@router.message(F.text)
async def auto_generate(
    message: Message,
    state: FSMContext,
    gemini_service: GeminiService,
    pollinations_service: PollinationsService,
):
    await state.set_state(GenerationStates.waiting_for_prompt)
    await process_prompt(message, state, gemini_service, pollinations_service)


async def _do_generation(
    message: Message,
    state: FSMContext,
    pollinations: PollinationsService,
    original_prompt: str,
    final_prompt: str,
    status_msg: Message | None = None,
    source_chat: Message | None = None,
    user_id: int | None = None,
    username: str | None = None,
):
    bot: Bot = message.bot  # type: ignore[assignment]
    target = source_chat or message
    if user_id is None:
        user_id = message.from_user.id
    if username is None and message.from_user:
        username = message.from_user.username

    # Get user's selected model
    model = await get_user_model(user_id)
    model_info = MODELS.get(model, MODELS["flux"])

    # Check daily limit
    if model_info["limit"] > 0:
        used = await get_model_usage_today(user_id, model)
        if used >= model_info["limit"]:
            await state.clear()
            text = (
                f"⚠️ Лимит модели <b>{model_info['emoji']} {model_info['name']}</b> "
                f"исчерпан на сегодня ({model_info['limit']}/{model_info['limit']}).\n\n"
                "Смените модель в настройках или попробуйте завтра."
            )
            if status_msg:
                await status_msg.edit_text(text, reply_markup=main_menu_kb())
            else:
                await target.answer(text, reply_markup=main_menu_kb())
            return

    if status_msg is None:
        status_msg = await target.answer(
            f"🎨 Генерирую ({model_info['emoji']} {model_info['name']})..."
        )
    else:
        try:
            await status_msg.edit_text(
                f"🎨 Генерирую ({model_info['emoji']} {model_info['name']})..."
            )
        except Exception:
            pass

    image_data = await pollinations.generate_image(final_prompt, model=model)
    await state.clear()

    if image_data is None:
        await status_msg.edit_text(
            "😔 Не удалось сгенерировать изображение. Попробуйте позже.",
            reply_markup=main_menu_kb(),
        )
        return

    # Track usage
    await add_model_usage(user_id, model)
    await add_generation(user_id, original_prompt, final_prompt)

    # Show remaining
    remaining_text = ""
    if model_info["limit"] > 0:
        used = await get_model_usage_today(user_id, model)
        remaining = model_info["limit"] - used
        remaining_text = f"\n{model_info['emoji']} {model_info['name']} — осталось {remaining}/{model_info['limit']}"

    photo = BufferedInputFile(image_data, filename="generation.png")
    caption = f"🎨 {original_prompt[:900]}"
    await target.answer_photo(photo=photo, caption=caption)

    try:
        await status_msg.delete()
    except Exception:
        pass

    await target.answer(
        f"Напишите новый запрос или выберите действие:{remaining_text}",
        reply_markup=main_menu_kb(),
    )

    # Log in background to not delay response
    asyncio.create_task(log_generation(
        bot,
        user_id,
        username,
        original_prompt,
        final_prompt,
        image_data,
        model=model,
    ))
