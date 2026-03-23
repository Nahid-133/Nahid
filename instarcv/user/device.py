from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from database import get_db_session, close_db_session, upsert_user_device, get_user_device_token
from user.states import UserStates
from user.keyboards import get_device_management_keyboard
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("set_device"))
@router.message(F.text == "📱 Set Device")
async def cmd_set_device(message: Message, state: FSMContext):
    user_id = message.from_user.id
    session = get_db_session()

    try:
        current_token = get_user_device_token(session, user_id)

        if current_token:
            masked_token = f"{current_token[:5]}...{current_token[-4:]}" if len(current_token) > 10 else "***"

            await message.answer(
                f"📱 <b>Device Already Registered</b>\n\n"
                f"Your current token:\n<code>{masked_token}</code>\n\n"
                f"Do you want to replace it with a new one?",
                reply_markup=get_device_management_keyboard(),
                parse_mode="HTML"
            )
            await state.clear()
        else:
            await message.answer(
                "📱 <b>Register Device</b>\n\n"
                "You don't have a device token set.\n"
                "Please send your FCM Device Token to register for notifications:",
                parse_mode="HTML"
            )
            await state.set_state(UserStates.waiting_device_token)

    except Exception as e:
        logger.error(f"Error in set_device check: {e}")
        await message.answer("❌ An error occurred.")
    finally:
        close_db_session(session)

@router.callback_query(F.data == "replace_device_token")
async def cb_replace_device(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔄 <b>Update Device Token</b>\n\n"
        "Please send the new FCM Device Token now:",
        parse_mode="HTML"
    )
    await state.set_state(UserStates.waiting_device_token)
    await callback.answer()

@router.callback_query(F.data == "cancel_device_update")
async def cb_cancel_device(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✅ Operation cancelled. Your existing token is kept.")
    await state.clear()
    await callback.answer()

@router.message(UserStates.waiting_device_token)
async def process_device_token(message: Message, state: FSMContext):
    token = message.text.strip()
    user_id = message.from_user.id

    if len(token) < 20 or " " in token:
        await message.answer("⚠️ Invalid token format. Please send a valid FCM device token.")
        return

    session = get_db_session()
    try:
        upsert_user_device(session, user_id, token)
        await message.answer("✅ Your device token has been updated successfully!")
    except Exception as e:
        logger.error(f"Error saving token: {e}")
        await message.answer(f"❌ Error saving token: {e}")
        session.rollback()
    finally:
        close_db_session(session)

    await state.clear()