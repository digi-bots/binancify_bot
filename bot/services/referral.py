from bot.config import BOT_USERNAME

def generate_referral_link(user_id: int) -> str:
    return f"https://t.me/{BOT_USERNAME}?start={user_id}"
