from aiogram.fsm.state import StatesGroup, State


class GenerationStates(StatesGroup):
    waiting_for_prompt = State()
    waiting_for_clarification = State()
