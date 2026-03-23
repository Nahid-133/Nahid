import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from sqlalchemy import func

from database import get_db_session, is_admin_by_telegram_id
from models import PaymentMethod
from .utils import check_admin

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "💳 Payment Methods")
async def handle_payment_methods_admin(message: types.Message):
    """Show payment methods management"""
    if not await check_admin(message):
        return

    session = get_db_session()
    try:
        methods = session.query(PaymentMethod).order_by(PaymentMethod.display_order).all()

        msg = "💳 **Payment Methods:**\n\n"
        for method in methods:
            status = "✅" if method.is_active else "❌"
            msg += f"{status} `{method.method_name}` (Order: {method.display_order})\n"

        msg += "\n**Commands:**\n"
        msg += "`/addmethod NAME` - Add method\n"
        msg += "`/delmethod NAME` - Delete method\n"
        msg += "`/togglemethod NAME` - Enable/Disable"

        await message.answer(msg, parse_mode='Markdown')

    finally:
        session.close()


@router.message(Command("addmethod"))
async def cmd_add_method(message: types.Message):
    """Add payment method"""
    session = get_db_session()
    try:
        if not is_admin_by_telegram_id(session, message.from_user.id):
            await message.answer("❌ Admin access required.")
            return

        parts = message.text.split(maxsplit=1)
        if len(parts) != 2:
            await message.answer(
                "❌ Invalid format.\n"
                "Use: `/addmethod MethodName`\n"
                "Example: `/addmethod Nagad`",
                parse_mode='Markdown'
            )
            return

        method_name = parts[1].strip()

        exists = session.query(PaymentMethod).filter_by(method_name=method_name).first()
        if exists:
            await message.answer(f"❌ Payment method `{method_name}` already exists.", parse_mode='Markdown')
            return

        max_order = session.query(func.max(PaymentMethod.display_order)).scalar() or 0

        new_method = PaymentMethod(
            method_name=method_name,
            is_active=True,
            display_order=max_order + 1
        )
        session.add(new_method)
        session.commit()

        await message.answer(f"✅ Payment method `{method_name}` added!", parse_mode='Markdown')

    finally:
        session.close()