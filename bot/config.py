import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
SQLITE_DB_PATH = "database/bot.db"
DATABASE_URL = os.getenv("DATABASE_URL")

DEFAULT_SETTINGS = {
    "channel_username": "@binancify_announcements",
    "group_username": "@binancify_chat",
    "group_send_text": "Hello Binancify",
    "website_registration_url": "https://example.com/register",
    "website_instruction": "Register on the website and provide your website username.",
    "joining_reward": "1.0",
    "referral_reward": "1.0",
    "min_referrals_withdraw": "5",
    "total_reward_pool": "10,000 USDT",
    # New display stats (editable by admin)
    "display_registered_users": "300+",
    "display_completed_payments": "100+",
    "display_pending_payments": "200",
}

settings_cache: dict = {}
