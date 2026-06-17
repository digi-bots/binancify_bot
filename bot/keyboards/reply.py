from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Balance")],
        [KeyboardButton(text="💸 Withdraw"), KeyboardButton(text="👮 Refer & Earn")]
    ],
    resize_keyboard=True
)
