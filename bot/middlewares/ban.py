from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot.database.models import User
from sqlalchemy import select

class BanMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        if user_id:
            session = data.get("session")
            if session:
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if user and user.banned:
                    if isinstance(event, Message):
                        await event.answer("🚫 You are banned.")
                    return
        return await handler(event, data)
