"""
Configuration Module
"""
import pytz

from dotenv import load_dotenv
import os
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
PROXY_URL = None

FCM_PROJECT_ID = "coockiesinstaserver"
ENC_FILE_PATH = "service-account.enc"
CREDS_DECRYPT_KEY="Paa2ddXbU+8xIHicjQMfqqDVbdt2I666P1cT2ttdGgo="
DHAKA_TZ = pytz.timezone('Asia/Dhaka')

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "turjaun"

DEFAULT_START_HOUR = 16
DEFAULT_START_MINUTE = 0
DEFAULT_END_HOUR = 10
DEFAULT_END_MINUTE = 0

CHANNEL_LINK = "https://t.me/earning_zne"
REPORT_FOOTER_MSG = (
    f"📍 *Verify results on our* [Telegram Channel]({CHANNEL_LINK})\n"
    "🔎 `Report any faults to the administrator`"
)


DEFAULT_PAYMENT_METHODS = ["Bkash", "Rocket"]

LOG_FILE = "bot_log.txt"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"