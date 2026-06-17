from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def continue_button():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Continue ▶️", callback_data="start_registration"))
    return builder.as_markup()

def get_task_step1_buttons():
    # This function now depends on dynamic settings, so we import here (or inside handler).
    # We'll import settings_cache inside the handler to keep this module clean.
    # So we'll define a factory that takes parameters, or build inline in the handler.
    # For simplicity, we'll build it in the handler. This function can be removed.
    pass

def withdraw_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Withdraw Now", callback_data="request_withdraw")]
    ])

def admin_panel():
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Users", callback_data="admin_users")
    builder.button(text="📤 Withdrawals", callback_data="admin_withdrawals")
    builder.button(text="⏳ Pending", callback_data="admin_pending")
    builder.button(text="📢 Broadcast", callback_data="admin_broadcast")
    builder.button(text="💰 Add Balance", callback_data="admin_addbal")
    builder.button(text="💸 Remove Balance", callback_data="admin_rembal")
    builder.button(text="🚫 Ban", callback_data="admin_ban")
    builder.button(text="✅ Unban", callback_data="admin_unban")
    builder.button(text="📥 Export CSV", callback_data="admin_export")
    builder.button(text="⚙️ Settings", callback_data="admin_settings")
    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup()
