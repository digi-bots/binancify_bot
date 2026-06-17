from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    waiting_for_telegram_username = State()
    waiting_for_website_username = State()
    waiting_for_wallet = State()
