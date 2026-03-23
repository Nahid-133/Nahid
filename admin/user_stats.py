import logging
from aiogram import Router, F, types

from database import get_db_session
from models import UserPayment, UserAccount, AdminAccount
from .utils import check_admin, get_target_date

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "👤 User Stats")
async def handle_user_stats(message: types.Message):
    """Show user statistics including specific target date progress"""
    if not await check_admin(message):
        return

    session = get_db_session()
    try:
        target_date, is_open = get_target_date(session)
        target_date_str = target_date.strftime('%Y-%m-%d')

        total_users = session.query(UserPayment.sender_id).distinct().count()
        total_accounts_lifetime = session.query(UserAccount).count()

        target_users_count = session.query(UserAccount.sender_id)\
            .filter_by(entry_date=target_date).distinct().count()

        target_user_accs = session.query(UserAccount)\
            .filter_by(entry_date=target_date).count()

        target_admin_accs = session.query(AdminAccount)\
            .filter_by(entry_date=target_date).count()

        status_icon = "🟢 Submission Open" if is_open else "🔴 Submission Closed"

        msg = (
            "👤 **User Statistics**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📅 **Target Date:** `{target_date_str}`\n"
            f"⏰ **Status:** {status_icon}\n\n"
            f"📊 **Target Date Progress:**\n"
            f"• Users Active: `{target_users_count}`\n"
            f"• User Accounts: `{target_user_accs}`\n"
            f"• Admin Accounts: `{target_admin_accs}`\n\n"
            f"📜 **Lifetime Data:**\n"
            f"• Total Unique Users: `{total_users}`\n"
            f"• Total Accounts (All Time): `{total_accounts_lifetime}`\n"
            f"━━━━━━━━━━━━━━━━━━"
        )

        await message.answer(msg, parse_mode='Markdown')

    finally:
        session.close()