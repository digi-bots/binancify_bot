from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from bot.config import DB_TYPE, DATABASE_URL, SQLITE_DB_PATH

if DB_TYPE == "postgresql":
    engine = create_async_engine(DATABASE_URL, echo=False)
else:
    engine = create_async_engine(f"sqlite+aiosqlite:///{SQLITE_DB_PATH}", echo=False)

async_session = async_sessionmaker(engine, expire_on_commit=False)
