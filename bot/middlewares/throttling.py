import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

RATE_LIMIT = 1  # seconds

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self.last_update = {}

    async def __call__(self, handler, event, data):
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return await handler(event, data)

        now = time.time()
        if user_id in self.last_update:
            if now - self.last_update[user_id] < RATE_LIMIT:
                return  # ignore
        self.last_update[user_id] = now
        return await handler(event, data)
