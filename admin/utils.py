"""
Utility Functions for Admin Module
"""
import json
import logging
from datetime import datetime, time, timedelta
from sqlalchemy import func
import pytz
try:
    from config import DHAKA_TZ
except ImportError:
    import pytz
    DHAKA_TZ = pytz.timezone('Asia/Dhaka')

from database import (
    get_db_session,
    is_admin_by_telegram_id,
    get_active_time_config,
    get_all_price_tiers
)

logger = logging.getLogger(__name__)


def get_dhaka_now():
    """Get current time in Dhaka timezone"""
    return datetime.now(DHAKA_TZ)


def get_target_date(session):
    """
    Determines the target date for submission based on the time window.

    Returns:
        tuple: (target_date, is_within_window)
    """
    config = get_active_time_config(session)
    if not config:
        logger.error("No active time configuration found")
        return datetime.now(DHAKA_TZ).date(), False

    now_time = get_dhaka_now().time()
    now_date = get_dhaka_now().date()

    start_time = time(config.start_hour, config.start_minute)
    end_time = time(config.end_hour, config.end_minute)

    is_night_shift = start_time > end_time

    if is_night_shift:
        if now_time >= start_time:
            return now_date + timedelta(days=1), True
        elif now_time <= end_time:
            return now_date, True
        else:
            return now_date, False
    else:
        if start_time <= now_time <= end_time:
            return now_date, True
        else:
            return now_date, False


def calculate_total(ok_count, session):
    """
    Calculate price per OK and total amount based on OK count

    Returns:
        tuple: (price_per_ok, total_amount)
    """
    tiers = get_all_price_tiers(session)

    if not tiers:
        return 0.0, 0.0

    for tier in tiers:
        if tier.min_ok <= ok_count <= tier.max_ok:
            total = ok_count * tier.price_per_ok
            return tier.price_per_ok, total

    return 0.0, 0.0


def format_time_window(config):
    """Format time window for display"""
    if not config:
        return "Not configured"

    return f"{config.start_hour:02d}:{config.start_minute:02d} - {config.end_hour:02d}:{config.end_minute:02d}"


def parse_payment_data(payment_json_str):
    """Parse payment JSON string to dict"""
    if not payment_json_str:
        return {}
    try:
        return json.loads(payment_json_str)
    except:
        return {}


def serialize_payment_data(payment_dict):
    """Serialize payment dict to JSON string"""
    return json.dumps(payment_dict)


def format_payment_info(payment_data):
    """Format payment data for display"""
    if not payment_data:
        return "No payment info"

    lines = []
    for method, number in payment_data.items():
        if number and number != "Not Provided":
            lines.append(f"   {method}: `{number}`")

    return "\n".join(lines) if lines else "No payment info"


async def check_admin(message_or_query):
    """
    Check if user is admin.
    Works with Message or CallbackQuery.
    """
    session = get_db_session()
    try:
        user_id = message_or_query.from_user.id
        is_admin_user = is_admin_by_telegram_id(session, user_id)

        if not is_admin_user:
            msg = "❌ Access denied. Admin login required.\nUse /admin to login."
            if hasattr(message_or_query, 'answer'):
                await message_or_query.answer(msg, show_alert=True)
            else:
                await message_or_query.answer(msg)
        return is_admin_user
    except Exception as e:
        logger.error(f"Error in check_admin: {e}")
        return False
    finally:
        session.close()