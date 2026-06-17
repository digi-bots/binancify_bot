from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from bot.database import async_session
from bot.database.models import User, Withdrawal
from bot.services.referral import generate_referral_link
from bot.keyboards.reply import main_menu
from bot.keyboards.inline import withdraw_button
from bot.config import settings_cache

router = Router()

@router.message(F.text == "💰 Balance")
async def show_balance(message: Message):
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            await message.answer("❌ You haven't started yet. Use /start")
            return
        await message.answer(
            f"💰 <b>Your Balance</b>\n\n"
            f"Balance: <b>{user.balance:.2f} USDT</b>\n"
            f"Referral Balance: <b>{user.referral_balance:.2f} USDT</b>\n"
            f"Total: <b>{user.total_balance:.2f} USDT</b>\n"
            f"Total Referrals: <b>{user.referral_count}</b>"
        )

@router.message(F.text == "👮 Refer & Earn")
async def refer_earn(message: Message):
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            await message.answer("❌ Start the bot first with /start")
            return
        link = generate_referral_link(user.id)
        min_ref = int(settings_cache.get("min_referrals_withdraw", "5"))
        remaining = max(0, min_ref - user.referral_count)
        ref_reward = settings_cache.get("referral_reward", "1.0")
        await message.answer(
            f"👥 <b>Refer & Earn</b>\n\n"
            f"Referral Reward: <b>{ref_reward} USDT</b> per friend\n\n"
            f"🔗 Your referral link:\n{link}\n\n"
            f"Total referrals: <b>{user.referral_count}</b>\n"
            f"More referrals needed to unlock withdrawal: <b>{remaining}</b>"
        )

@router.message(F.text == "💸 Withdraw")
async def withdraw_request(message: Message):
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            await message.answer("❌ Start first /start")
            return
        if not user.completed_tasks:
            await message.answer("❌ You must complete all tasks first.")
            return
        if not user.wallet_address:
            await message.answer("❌ You haven't set a wallet. Complete registration.")
            return
        min_ref = int(settings_cache.get("min_referrals_withdraw", "5"))
        if user.referral_count < min_ref:
            await message.answer(
                f"❌ You need at least {min_ref} referrals to unlock withdrawal.\n"
                f"Currently you have {user.referral_count}."
            )
            return
        total = user.total_balance
        if total <= 0:
            await message.answer("❌ Nothing to withdraw.")
            return
        await message.answer(
            f"💸 You are about to withdraw <b>{total:.2f} USDT</b> to your TRC-20 wallet:\n"
            f"<code>{user.wallet_address}</code>\n\n"
            "Click below to confirm.",
            reply_markup=withdraw_button()
        )

@router.callback_query(F.data == "request_withdraw")
async def confirm_withdraw(callback: CallbackQuery):
    await callback.answer()
    async with async_session() as session:
        user = await session.get(User, callback.from_user.id)
        if not user or user.total_balance <= 0:
            await callback.message.edit_text("❌ No balance to withdraw.")
            return
        amount = user.total_balance
        wd = Withdrawal(
            user_id=user.id,
            wallet=user.wallet_address,
            amount=amount,
            status="pending"
        )
        session.add(wd)
        user.balance = 0.0
        user.referral_balance = 0.0
        user.update_total_balance()
        await session.commit()
        await callback.message.edit_text(
            f"✅ Withdrawal request for {amount:.2f} USDT created.\n"
            "It will be processed soon."
        )
