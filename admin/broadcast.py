from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from database import get_db_session, close_db_session, get_all_device_tokens, is_user_admin
from admin.states import AdminStates
from utils import broadcast_fcm_notifications
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("broadcast"))
@router.message(F.text == "📢 Broadcast")
async def cmd_broadcast(message: Message, state: FSMContext):
    session = get_db_session()
    try:
        if not is_user_admin(session, message.from_user.id):
            await message.answer("⛔ Access Denied.")
            return

        await message.answer("📢 Enter the notification message to send to all users:")
        await state.set_state(AdminStates.waiting_broadcast_message)
    finally:
        close_db_session(session)

@router.message(AdminStates.waiting_broadcast_message)
async def process_broadcast(message: Message, state: FSMContext):
    broadcast_text = message.text
    status_msg = await message.answer("🚀 Starting broadcast...")

    session = get_db_session()
    try:
        tokens = get_all_device_tokens(session)
        if not tokens:
            await status_msg.edit_text("No registered devices found.")
            return

        count = await broadcast_fcm_notifications(tokens, "📢 Admin Update", broadcast_text)
        await status_msg.edit_text(f"✅ Notification sent to {count}/{len(tokens)} devices.")
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await message.answer(f"Error: {e}")
    finally:
        close_db_session(session)
        await state.clear()