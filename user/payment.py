"""
Payment Handlers
"""
import logging
from aiogram import Router, types, F
from aiogram.filters import Command

from models import UserPayment
from database import get_db_session, get_active_payment_methods
from utils import get_target_date, parse_payment_data, serialize_payment_data

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "💰 Payment Methods")
async def handle_payment_methods_button(message: types.Message):
    """Show and update payment methods"""
    session = get_db_session()
    try:
        methods = get_active_payment_methods(session)

        if not methods:
            await message.answer("❌ No payment methods available.")
            return

        target_date, _ = get_target_date(session)
        payment = session.query(UserPayment).filter_by(
            sender_id=message.from_user.id,
            entry_date=target_date
        ).first()

        current_data = parse_payment_data(payment.payment_data if payment else None)

        msg = f"💰 **Payment Methods** (Date: `{target_date.strftime('%Y-%m-%d')}`)\n\n"
        msg += "**Available Methods:**\n"

        for method in methods:
            current_value = current_data.get(method.method_name, "Not Set")
            msg += f"   {method.method_name}: `{current_value}`\n"

        msg += "\n**To Update:**\n"
        msg += "Send message in format:\n"
        for method in methods:
            msg += f"`/pay {method.method_name.lower()} : YOUR_NUMBER`\n"

        await message.answer(msg, parse_mode='Markdown')

    finally:
        session.close()


@router.message(Command("pay"))
async def handle_pay_command(message: types.Message):
    """Handle payment update command"""
    session = get_db_session()
    try:
        text = message.text.lower()
        sender_id = message.from_user.id
        full_username = message.from_user.username or "no_username"

        target_date, _ = get_target_date(session)

        methods = get_active_payment_methods(session)

        found_method = None
        number = None

        for method in methods:
            if method.method_name.lower() in text:
                found_method = method.method_name
                number = text.split(method.method_name.lower())[-1].replace(":", "").strip()
                break

        if not found_method:
            methods_str = ", ".join([m.method_name for m in methods])
            await message.reply(
                f"❌ **Invalid payment method.**\n\n"
                f"Available methods: {methods_str}\n"
                f"Use: `/pay methodname : number`",
                parse_mode='Markdown'
            )
            return

        payment = session.query(UserPayment).filter_by(
            sender_id=sender_id,
            entry_date=target_date
        ).first()

        if not payment:
            payment = UserPayment(
                sender_id=sender_id,
                entry_date=target_date,
                telegram_username=full_username,
                payment_data="{}"
            )
            session.add(payment)

        payment.telegram_username = full_username
        payment_dict = parse_payment_data(payment.payment_data)
        payment_dict[found_method] = number
        payment.payment_data = serialize_payment_data(payment_dict)

        session.commit()

        await message.reply(
            f"✅ **{found_method} number saved**\n\n"
            f"📅 Date: `{target_date.strftime('%Y-%m-%d')}`\n"
            f"💳 Number: `{number}`",
            parse_mode='Markdown'
        )

        logger.info(f"Payment updated: {full_username} ({sender_id}) set {found_method} to {number}")

    except Exception as e:
        logger.error(f"Pay command error: {e}")
        await message.reply("❌ Error saving payment info.")
        session.rollback()
    finally:
        session.close()