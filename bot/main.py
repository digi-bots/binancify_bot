import asyncio, logging, threading
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from flask import Flask
from bot.config import BOT_TOKEN
from bot.database.engine import engine, async_session
from bot.database.base import Base
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.middlewares.ban import BanMiddleware
from bot.handlers.start import router as start_router
from bot.handlers.registration import router as reg_router
from bot.handlers.menu import router as menu_router
from bot.handlers.admin import router as admin_router
from bot.handlers.errors import router as error_router
from bot.utils.helpers import load_settings_from_db

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

def run_flask():
    app.run(host='0.0.0.0', port=10000)

async def main():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Load settings into cache
    await load_settings_from_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware setup
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())

    # Session injection middleware
    async def session_middleware(handler, event, data):
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)

    dp.message.middleware(session_middleware)
    dp.callback_query.middleware(session_middleware)

    # Include routers
    dp.include_router(admin_router)   # admin first to catch /admin
    dp.include_router(start_router)
    dp.include_router(reg_router)
    dp.include_router(menu_router)
    dp.include_router(error_router)

    # Run Flask in background thread (for Render health check)
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
