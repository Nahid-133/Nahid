"""
Start Command Handler
"""
import logging
from aiogram import Router, types
from aiogram.filters import Command

from user.keyboards import get_user_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    user_name = message.from_user.first_name or "User"

    welcome_msg = (
        f"👋 **Welcome {user_name}!**\n\n"
        f"🤖 This bot helps you submit accounts and track your reports.\n\n"
        f"**Features:**\n"
        f"📁 Submit account files (JSON format)\n"
        f"📊 View your submission reports\n"
        f"💰 Update payment information\n"
        f"📖 View submission manual\n\n"
        f"Use the buttons below to get started! 👇"
    )

    await message.answer(welcome_msg, parse_mode='Markdown', reply_markup=get_user_keyboard())