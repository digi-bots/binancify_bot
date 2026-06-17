import io, csv, logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from bot.database import async_session
from bot.database.models import User, Withdrawal
from bot.keyboards.inline import admin_panel
from bot.config import ADMIN_IDS, settings_cache
from bot.utils.helpers import update_setting

router = Router()

class AdminStates(StatesGroup):
    waiting_for_add_balance_user = State()
    waiting_for_add_balance_amount = State()
    waiting_for_remove_balance_user = State()
    waiting_for_remove_balance_amount = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()

class BroadcastStates(StatesGroup):
    waiting_for_photos = State()
    waiting_for_title_body = State()
    waiting_for_buttons = State()

class SettingsStates(StatesGroup):
    waiting_for_key = State()
    waiting_for_value = State()

def admin_only(func):
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id not in ADMIN_IDS:
            return
        return await func(message, *args, **kwargs)
    return wrapper

@router.message(Command("admin"))
@admin_only
async def admin_cmd(message: Message):
    await message.answer("🔐 Admin Panel", reply_markup=admin_panel())

# ---------- Statistics ----------
@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    async with async_session() as session:
        count = await session.scalar(select(func.count(User.id)))
    await callback.message.edit_text(f"👥 Total users: {count}", reply_markup=admin_panel())
    await callback.answer()

@router.callback_query(F.data == "admin_withdrawals")
async def admin_withdrawals(callback: CallbackQuery):
    async with async_session() as session:
        total = await session.scalar(select(func.count(Withdrawal.id)))
    await callback.message.edit_text(f"📤 Total withdrawals: {total}", reply_markup=admin_panel())
    await callback.answer()

@router.callback_query(F.data == "admin_pending")
async def admin_pending(callback: CallbackQuery):
    async with async_session() as session:
        pending = await session.scalar(select(func.count(Withdrawal.id)).where(Withdrawal.status == "pending"))
    await callback.message.edit_text(f"⏳ Pending withdrawals: {pending}", reply_markup=admin_panel())
    await callback.answer()

# ---------- Balance management ----------
@router.callback_query(F.data == "admin_addbal")
async def admin_addbal(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send user ID:")
    await state.set_state(AdminStates.waiting_for_add_balance_user)
    await callback.answer()

@router.message(AdminStates.waiting_for_add_balance_user)
@admin_only
async def addbal_user(message: Message, state: FSMContext):
    uid = message.text.strip()
    if not uid.isdigit():
        await message.answer("Invalid ID.")
        return
    await state.update_data(uid=int(uid))
    await message.answer("Send amount to add:")
    await state.set_state(AdminStates.waiting_for_add_balance_amount)

@router.message(AdminStates.waiting_for_add_balance_amount)
@admin_only
async def addbal_amount(message: Message, state: FSMContext):
    try:
        amt = float(message.text)
    except:
        await message.answer("Invalid amount.")
        return
    data = await state.get_data()
    uid = data["uid"]
    async with async_session() as session:
        user = await session.get(User, uid)
        if user:
            user.balance += amt
            user.update_total_balance()
            await session.commit()
            await message.answer(f"Added {amt} USDT to user {uid}.")
        else:
            await message.answer("User not found.")
    await state.clear()

@router.callback_query(F.data == "admin_rembal")
async def admin_rembal(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send user ID:")
    await state.set_state(AdminStates.waiting_for_remove_balance_user)
    await callback.answer()

@router.message(AdminStates.waiting_for_remove_balance_user)
@admin_only
async def rembal_user(message: Message, state: FSMContext):
    uid = message.text.strip()
    if not uid.isdigit():
        await message.answer("Invalid ID.")
        return
    await state.update_data(uid=int(uid))
    await message.answer("Send amount to remove:")
    await state.set_state(AdminStates.waiting_for_remove_balance_amount)

@router.message(AdminStates.waiting_for_remove_balance_amount)
@admin_only
async def rembal_amount(message: Message, state: FSMContext):
    try:
        amt = float(message.text)
    except:
        await message.answer("Invalid amount.")
        return
    data = await state.get_data()
    uid = data["uid"]
    async with async_session() as session:
        user = await session.get(User, uid)
        if user:
            user.balance = max(0, user.balance - amt)
            user.update_total_balance()
            await session.commit()
            await message.answer(f"Removed {amt} USDT from user {uid}.")
        else:
            await message.answer("User not found.")
    await state.clear()

# ---------- Ban / Unban ----------
@router.callback_query(F.data == "admin_ban")
async def admin_ban(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send user ID to ban:")
    await state.set_state(AdminStates.waiting_for_ban_id)
    await callback.answer()

@router.message(AdminStates.waiting_for_ban_id)
@admin_only
async def ban_user(message: Message, state: FSMContext):
    uid = message.text.strip()
    if not uid.isdigit():
        await message.answer("Invalid ID.")
        return
    async with async_session() as session:
        user = await session.get(User, int(uid))
        if user:
            user.banned = True
            await session.commit()
            await message.answer(f"User {uid} banned.")
        else:
            await message.answer("User not found.")
    await state.clear()

@router.callback_query(F.data == "admin_unban")
async def admin_unban(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Send user ID to unban:")
    await state.set_state(AdminStates.waiting_for_unban_id)
    await callback.answer()

@router.message(AdminStates.waiting_for_unban_id)
@admin_only
async def unban_user(message: Message, state: FSMContext):
    uid = message.text.strip()
    if not uid.isdigit():
        await message.answer("Invalid ID.")
        return
    async with async_session() as session:
        user = await session.get(User, int(uid))
        if user:
            user.banned = False
            await session.commit()
            await message.answer(f"User {uid} unbanned.")
        else:
            await message.answer("User not found.")
    await state.clear()

# ---------- Export CSV ----------
@router.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery):
    async with async_session() as session:
        users = await session.scalars(select(User))
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "telegram_username", "website_username", "wallet", "balance", "referral_balance", "total", "referrals", "completed"])
        for u in users:
            writer.writerow([u.id, u.telegram_username_input, u.twitter_username, u.wallet_address,
                             u.balance, u.referral_balance, u.total_balance, u.referral_count, u.completed_tasks])
        await callback.message.answer_document(
            document=io.BytesIO(output.getvalue().encode()),
            filename="users.csv"
        )
    await callback.answer()

# ---------- Broadcast (image + title + body + buttons) ----------
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📢 <b>Broadcast Setup</b>\n\n"
        "Step 1/3: Send one or more photos.\n"
        "Send all photos one by one. When finished, send /done"
    )
    await state.set_state(BroadcastStates.waiting_for_photos)
    await state.update_data(photos=[])
    await callback.answer()

@router.message(BroadcastStates.waiting_for_photos, F.photo)
async def collect_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Photo received ({len(photos)} total). Send more or /done to proceed.")

@router.message(BroadcastStates.waiting_for_photos, F.text == "/done")
async def done_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("photos"):
        await message.answer("❌ At least one photo is required. Send a photo.")
        return
    await message.answer(
        "📝 <b>Step 2/3:</b>\n"
        "Send the title and body in this format:\n\n"
        "<b>Your Bold Title</b>\nBody text here...\n\n"
        "You can use HTML tags."
    )
    await state.set_state(BroadcastStates.waiting_for_title_body)

@router.message(BroadcastStates.waiting_for_title_body)
async def collect_title_body(message: Message, state: FSMContext):
    text = message.text or message.caption
    if not text:
        await message.answer("Please send text message with title and body.")
        return
    await state.update_data(title_body=text)
    await message.answer(
        "🔘 <b>Step 3/3:</b> Add inline buttons (optional).\n"
        "Format: one button per line:\n"
        "<code>Button Name - https://url.com</code>\n\n"
        "Send '-' if you don't want any buttons."
    )
    await state.set_state(BroadcastStates.waiting_for_buttons)

@router.message(BroadcastStates.waiting_for_buttons)
async def finalize_broadcast(message: Message, state: FSMContext, bot: Bot):
    buttons_raw = message.text.strip()
    inline_keyboard = []
    if buttons_raw and buttons_raw != "-":
        lines = buttons_raw.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(" - ", 1)
            if len(parts) == 2:
                name, url = parts[0].strip(), parts[1].strip()
                inline_keyboard.append([InlineKeyboardButton(text=name, url=url)])
            else:
                await message.answer(f"⚠️ Invalid format: {line}, skipping.")
    data = await state.get_data()
    photos = data["photos"]
    title_body = data["title_body"]

    async with async_session() as session:
        users = await session.scalars(select(User.id))
        count = 0
        for uid in users:
            try:
                reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard) if inline_keyboard else None
                await bot.send_photo(uid, photo=photos[0], caption=title_body, parse_mode="HTML", reply_markup=reply_markup)
                for ph in photos[1:]:
                    await bot.send_photo(uid, photo=ph)
                count += 1
            except Exception as e:
                logging.warning(f"Failed to send to {uid}: {e}")
    await message.answer(f"✅ Broadcast sent to {count} users.")
    await state.clear()

# ---------- Settings ----------
@router.callback_query(F.data == "admin_settings")
async def admin_settings_start(callback: CallbackQuery, state: FSMContext):
    keys_list = "\n".join([f"<code>{k}</code>" for k in settings_cache.keys()])
    await callback.message.edit_text(
        f"⚙️ <b>Change Settings</b>\n\n"
        f"Available keys:\n{keys_list}\n\n"
        f"Send the key you want to change:"
    )
    await state.set_state(SettingsStates.waiting_for_key)
    await callback.answer()

@router.message(SettingsStates.waiting_for_key)
@admin_only
async def settings_key_entered(message: Message, state: FSMContext):
    key = message.text.strip().lower()
    if key not in settings_cache:
        await message.answer("❌ Invalid key. Please choose from the list.")
        return
    await state.update_data(key=key)
    current_val = settings_cache.get(key, "")
    await message.answer(f"Current value: <code>{current_val}</code>\nSend new value:")
    await state.set_state(SettingsStates.waiting_for_value)

@router.message(SettingsStates.waiting_for_value)
@admin_only
async def settings_value_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data["key"]
    new_value = message.text.strip()
    await update_setting(key, new_value)
    await message.answer(f"✅ Setting <code>{key}</code> updated to <code>{new_value}</code>.")
    await state.clear()
