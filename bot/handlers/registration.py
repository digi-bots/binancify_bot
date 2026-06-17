from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy import select
from bot.database import async_session
from bot.database.models import User
from bot.states.registration import Registration
from bot.services.validation import is_valid_wallet
from bot.keyboards.reply import main_menu
from bot.config import settings_cache

router = Router()

# ---------- Membership check ----------
async def check_membership(user_id: int, bot: Bot) -> tuple:
    ch_username = settings_cache.get("channel_username", "@binancify_announcements")
    gr_username = settings_cache.get("group_username", "@binancify_chat")
    try:
        ch = await bot.get_chat_member(f"@{ch_username.lstrip('@')}", user_id)
        joined_channel = ch.status not in ['left', 'kicked']
    except:
        joined_channel = False
    try:
        gr = await bot.get_chat_member(f"@{gr_username.lstrip('@')}", user_id)
        joined_group = gr.status not in ['left', 'kicked']
    except:
        joined_group = False
    return joined_channel, joined_group

def get_task_buttons():
    ch = settings_cache.get("channel_username", "binancify_announcements").lstrip("@")
    gr = settings_cache.get("group_username", "binancify_chat").lstrip("@")
    website = settings_cache.get("website_registration_url", "https://example.com/register")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel", url=f"https://t.me/{ch}")],
        [InlineKeyboardButton(text="💬 Join Group", url=f"https://t.me/{gr}")],
        [InlineKeyboardButton(text="🌐 Register on Website", url=website)]
    ])

# ---------- Step 1 ----------
@router.callback_query(F.data == "start_registration")
async def start_registration(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    joined_ch, joined_gr = await check_membership(callback.from_user.id, bot)
    if not joined_ch or not joined_gr:
        await callback.message.answer(
            "❌ আপনি এখনো চ্যানেল বা গ্রুপে জয়েন করেননি। নিচের বাটন থেকে জয়েন করে আবার Continue চাপুন।",
            reply_markup=get_task_buttons()
        )
        return

    group_text = settings_cache.get("group_send_text", "Hello Binancify")
    await callback.message.answer(
        f"<b>Step 1: Verification</b>\n\n"
        f"✅ Channel joined\n"
        f"✅ Group joined\n\n"
        f"2️⃣ Send <code>{group_text}</code> in the group.\n\n"
        f"After completing, send me your Telegram username (e.g., @yourusername)"
    )
    await state.set_state(Registration.waiting_for_telegram_username)

# ---------- Collect Telegram username ----------
@router.message(StateFilter(Registration.waiting_for_telegram_username))
async def process_telegram_username(message: Message, state: FSMContext):
    username = message.text.strip()
    if not username.startswith("@"):
        await message.answer("❌ Please send a valid Telegram username starting with @")
        return
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if user:
            user.telegram_username_input = username
            await session.commit()

    website_url = settings_cache.get("website_registration_url", "https://example.com/register")
    instruction = settings_cache.get("website_instruction", "Register on the website and provide your website username.")
    await message.answer(
        f"✅ Telegram username saved!\n\n"
        f"<b>Step 2: Website Registration</b>\n"
        f"{instruction}\n\n"
        f"🔗 <a href='{website_url}'>Register here</a>\n\n"
        f"After registering, send me your <b>website username</b> (the username you created on the site)."
    )
    await state.set_state(Registration.waiting_for_website_username)

# ---------- Collect website username ----------
@router.message(StateFilter(Registration.waiting_for_website_username))
async def process_website_username(message: Message, state: FSMContext):
    web_username = message.text.strip()
    if not web_username or " " in web_username:
        await message.answer("❌ Please enter a valid website username (no spaces).")
        return
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if user:
            user.twitter_username = web_username  # reusing field
            await session.commit()

    await message.answer(
        "🌐 Website username saved!\n\n"
        "<b>Step 3: Wallet Address</b>\n"
        "Send your <b>TRC-20 wallet address</b> (starts with <code>T</code>, 34 characters).\n\n"
        "Example: <code>TLa2f6VPqDgRE67v1736q7bJ8Ray5wYjU7</code>"
    )
    await state.set_state(Registration.waiting_for_wallet)

# ---------- Collect wallet ----------
@router.message(StateFilter(Registration.waiting_for_wallet))
async def process_wallet(message: Message, state: FSMContext):
    wallet = message.text.strip()
    if not is_valid_wallet(wallet):
        await message.answer(
            "❌ Invalid TRC-20 wallet address.\n"
            "Make sure it starts with <code>T</code> and is 34 characters long.\n"
            "Please try again."
        )
        return

    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if user:
            user.wallet_address = wallet
            user.completed_tasks = True
            joining_reward = float(settings_cache.get("joining_reward", "1.0"))
            user.balance += joining_reward
            user.update_total_balance()
            await session.commit()
            await message.answer(
                f"🎉 <b>Congratulations!</b>\n"
                f"You earned {joining_reward} USDT as Joining Bonus.\n\n"
                "Use the menu below to check balance, refer friends, or withdraw.",
                reply_markup=main_menu
            )
    await state.clear()
