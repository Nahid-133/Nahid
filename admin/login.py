import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from database import get_db_session, verify_admin, update_admin_telegram_id, is_admin_by_telegram_id

from .states import AdminStates
from .keyboards import get_admin_keyboard
from .utils import check_admin

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    """Handle /admin command"""
    session = get_db_session()
    try:
        if is_admin_by_telegram_id(session, message.from_user.id):
            await message.answer(
                "✅ You are already logged in as admin!",
                reply_markup=get_admin_keyboard()
            )
            return

        await message.answer(
            "🔐",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(AdminStates.waiting_for_credentials)

    except Exception as e:
        logger.error(f"Error in cmd_admin: {e}")
        await message.answer("❌ Error accessing admin system.")
    finally:
        session.close()


@router.message(AdminStates.waiting_for_credentials)
async def process_admin_login(message: types.Message, state: FSMContext):
    """Process admin login credentials"""
    session = get_db_session()
    try:
        parts = message.text.strip().split()

        if len(parts) != 2:
            await message.answer(
                "❌ Invalid format.\n"
                "Please send: `username password`",
                parse_mode='Markdown'
            )
            return

        username, password = parts

        if verify_admin(session, username, password):
            update_admin_telegram_id(session, username, message.from_user.id)
            session.commit()

            await message.answer(
                "✅ **Login Successful!**\n\n"
                "Welcome to Admin Panel.",
                parse_mode='Markdown',
                reply_markup=get_admin_keyboard()
            )
            await state.clear()
            logger.info(f"Admin logged in: {username} (Telegram ID: {message.from_user.id})")
        else:
            await message.answer(
                "❌ **Invalid credentials!**\n\n"
                "Please try again or contact system administrator.",
                parse_mode='Markdown'
            )
            await state.clear()

    except Exception as e:
        logger.error(f"Error in process_admin_login: {e}")
        await message.answer("❌ Error processing login.")
    finally:
        session.close()