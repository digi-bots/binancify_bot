from sqlalchemy import select
from bot.database import async_session
from bot.database.models import BotSettings
from bot.config import DEFAULT_SETTINGS, settings_cache

async def load_settings_from_db():
    """Initialize settings cache from DB, or insert defaults if empty."""
    async with async_session() as session:
        result = await session.execute(select(BotSettings))
        rows = result.scalars().all()
        if not rows:
            for k, v in DEFAULT_SETTINGS.items():
                session.add(BotSettings(key=k, value=v))
                settings_cache[k] = v
            await session.commit()
        else:
            for row in rows:
                settings_cache[row.key] = row.value
            # Ensure any new default keys are added
            for k, v in DEFAULT_SETTINGS.items():
                if k not in settings_cache:
                    settings_cache[k] = v
                    session.add(BotSettings(key=k, value=v))
            await session.commit()

async def update_setting(key: str, value: str):
    """Update a setting in DB and cache."""
    async with async_session() as session:
        setting = await session.get(BotSettings, key)
        if setting:
            setting.value = value
        else:
            session.add(BotSettings(key=key, value=value))
        await session.commit()
    settings_cache[key] = value
