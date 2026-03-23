"""
Reports Handler
"""
import logging
from aiogram import Router, types, F
from sqlalchemy import func

from models import UserAccount, UserPayment, AdminAccount
from database import get_db_session
from utils import calculate_total

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "📊 My Reports")
async def handle_my_reports_button(message: types.Message):
    """Show user's last 5 reports by fetching actual dates from DB"""
    session = get_db_session()
    try:
        sender_id = message.from_user.id

        date_results = session.query(UserAccount.entry_date)\
            .filter_by(sender_id=sender_id)\
            .distinct()\
            .order_by(UserAccount.entry_date.desc())\
            .limit(5)\
            .all()

        if not date_results:
            await message.answer(
                "📊 **No Reports Found**\n\n"
                "You haven't submitted any files yet.",
                parse_mode='Markdown'
            )
            return

        reports = []
        dates_to_check = [d[0] for d in date_results]

        for check_date in dates_to_check:
            total_accounts = session.query(func.count(UserAccount.id)).filter_by(
                sender_id=sender_id,
                entry_date=check_date
            ).scalar()

            ok_count = session.query(func.count(AdminAccount.id)).filter(
                AdminAccount.sender_id == sender_id,
                AdminAccount.entry_date == check_date,
                AdminAccount.ok_status == True
            ).scalar()

            payment = session.query(UserPayment).filter_by(
                sender_id=sender_id,
                entry_date=check_date
            ).first()

            price_per_ok, total_money = calculate_total(ok_count, session)

            reports.append({
                'date': check_date.strftime('%Y-%m-%d'),
                'ok_count': ok_count,
                'total_accounts': total_accounts,
                
                
                'paid': payment.paid_status if payment else False
            })

        msg = "📊 **Your Recent Reports**\n"
        msg += "━━━━━━━━━━━━━━━━━━\n\n"

        for report in reports:
            paid_status = "✅ Paid" if report['paid'] else "⏳ Pending"
            msg += (
                f"📅 **Date:** `{report['date']}`\n"
                f"📥 Total: `{report['total_accounts']}` | ✅ OK: `{report['ok_count']}`\n"
                f"💰 Rate: `{report['price_per_ok']}` | 💵 Total: `{report['total_amount']:.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━\n"
            )

        await message.answer(msg, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error in My Reports: {e}", exc_info=True)
        await message.answer("❌ Error retrieving your reports.")
    finally:
        session.close()