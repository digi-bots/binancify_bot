from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from sqlalchemy import select
from bot.database import async_session
from bot.database.models import User
from bot.config import settings_cache
from bot.keyboards.inline import continue_button

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    total_pool = settings_cache.get("total_reward_pool", "10,000 USDT")
    joining_reward = settings_cache.get("joining_reward", "1.0")
    referral_reward = settings_cache.get("referral_reward", "1.0")
    reg_users = settings_cache.get("display_registered_users", "300+")
    completed = settings_cache.get("display_completed_payments", "100+")
    pending = settings_cache.get("display_pending_payments", "200")

    welcome_text = (
        f"🎉 Welcome to <b>Binancify</b> Airdrop!\n\n"
        f"📊 <b>Live Stats</b>\n"
        f"👥 Registered Users: {reg_users}\n"
        f"✅ Payments Completed: {completed}\n"
        f"⏳ Pending Payments: {pending}\n\n"
        f"🏆 <b>Total Reward Pool:</b> {total_pool}\n"
        f"💰 <b>Joining Reward:</b> {joining_reward} USDT\n"
        f"👥 <b>Referral Reward:</b> {referral_reward} USDT per friend\n\n"
        f"📌 <b>About Binancify:</b>\n"
        f"The next-generation DeFi platform backed by Binance Labs.\n"
        f"Complete simple tasks and earn real USDT rewards instantly!\n\n"
        f"Click <b>Continue</b> to begin verification."
    )

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalar_one_or_none()

        if not user:
            new_user = User(id=message.from_user.id)
            ref_id = command.args
            if ref_id and ref_id.isdigit():
                referrer_id = int(ref_id)
                if referrer_id != message.from_user.id:
                    referrer_result = await session.execute(select(User).where(User.id == referrer_id))
                    referrer = referrer_result.scalar_one_or_none()
                    if referrer and not referrer.banned:
                        new_user.referrer_id = referrer_id
                        ref_reward = float(settings_cache.get("referral_reward", "1.0"))
                        referrer.referral_count += 1
                        referrer.referral_balance += ref_reward
                        referrer.update_total_balance()
            session.add(new_user)
            await session.commit()

    await message.answer(welcome_text, reply_markup=continue_button())
