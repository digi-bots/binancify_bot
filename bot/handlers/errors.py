from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()

@router.errors()
async def error_handler(error: ErrorEvent):
    print(f"Update {error.update} caused error {error.exception}")
    return True
