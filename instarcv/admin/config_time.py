import logging
from aiogram import Router, F, types
from aiogram.filters import Command

from database import get_db_session, is_admin_by_telegram_id, get_active_time_config
from models import TimeConfig
from .utils import check_admin

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "⏰ Time Config")
async def handle_time_config(message: types.Message):
    """Show and manage time configuration"""
    if not await check_admin(message):
        return

    session = get_db_session()
    try:
        config = get_active_time_config(session)

        if config:
            msg = (
                "⏰ **Current Time Configuration**\n\n"
                f"Start: `{config.start_hour:02d}:{config.start_minute:02d}`\n"
                f"End: `{config.end_hour:02d}:{config.end_minute:02d}`\n\n"
                "To update, send:\n"
                "`/settime HH:MM HH:MM`\n\n"
                "Example: `/settime 16:00 10:00`"
            )
        else:
            msg = "❌ No time configuration found.\n\nUse `/settime HH:MM HH:MM` to set."

        await message.answer(msg, parse_mode='Markdown')

    finally:
        session.close()


@router.message(Command("settime"))
async def cmd_set_time(message: types.Message):
    """Set time configuration"""
    session = get_db_session()
    try:
        if not is_admin_by_telegram_id(session, message.from_user.id):
            await message.answer("❌ Admin access required.")
            return

        parts = message.text.split()
        if len(parts) != 3:
            await message.answer(
                "❌ Invalid format.\n"
                "Use: `/settime HH:MM HH:MM`\n"
                "Example: `/settime 16:00 10:00`",
                parse_mode='Markdown'
            )
            return

        try:
            start_parts = parts[1].split(':')
            end_parts = parts[2].split(':')

            start_hour = int(start_parts[0])
            start_minute = int(start_parts[1])
            end_hour = int(end_parts[0])
            end_minute = int(end_parts[1])

            if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59 and
                    0 <= end_hour <= 23 and 0 <= end_minute <= 59):
                raise ValueError("Invalid time values")

            session.query(TimeConfig).update({TimeConfig.is_active: False})

            new_config = TimeConfig(
                start_hour=start_hour,
                start_minute=start_minute,
                end_hour=end_hour,
                end_minute=end_minute,
                is_active=True
            )
            session.add(new_config)
            session.commit()

            await message.answer(
                f"✅ **Time configuration updated!**\n\n"
                f"Start: `{start_hour:02d}:{start_minute:02d}`\n"
                f"End: `{end_hour:02d}:{end_minute:02d}`",
                parse_mode='Markdown'
            )

            logger.info(f"Time config updated: {start_hour:02d}:{start_minute:02d} - {end_hour:02d}:{end_minute:02d}")

        except (ValueError, IndexError):
            await message.answer(
                "❌ Invalid time format.\n"
                "Use HH:MM format (24-hour)",
                parse_mode='Markdown'
            )

    finally:
        session.close()