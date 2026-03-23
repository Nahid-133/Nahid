"""
Manual Handler
"""
import logging
from aiogram import Router, types, F

from database import get_db_session, get_active_payment_methods
from utils import format_time_window

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "📖 Manual")
async def handle_manual_button(message: types.Message):
    """Show submission manual"""
    session = get_db_session()
    try:
        from database import get_active_time_config

        time_config = get_active_time_config(session)
        time_window = format_time_window(time_config)

        methods = get_active_payment_methods(session)
        methods_list = ", ".join([m.method_name for m in methods])

        manual = (
            "📖 **Submission Manual**\n\n"
            f"⏰ **Submission Window:** `{time_window}`\n\n"
            "**How to Submit Files:**\n"
            "1️⃣ Click '📁 Submit Files' button\n"
            "2️⃣ Send your JSON file(s) during submission window\n"
            "3️⃣ Bot will process and save your accounts\n\n"
            "**File Format:**\n"
            "JSON file with username and password fields:\n"
            "```json\n"
            "[\n"
            "  {\"username\": \"user1\", \"password\": \"pass1\"},\n"
            "  {\"username\": \"user2\", \"password\": \"pass2\"}\n"
            "]\n"
            "```\n\n"
            f"**Payment Methods:**\n{methods_list}\n\n"
            "**Update Payment Info:**\n"
            "`/pay methodname : number`\n"
            "Example: `/pay bkash : 01712345678`\n\n"
            "**View Reports:**\n"
            "Click '📊 My Reports' to see your last 5 days.\n\n"
            "❓ **Need Help?** Contact admin."
        )

        await message.answer(manual, parse_mode='Markdown')

    finally:
        session.close()