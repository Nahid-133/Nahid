import logging
from aiogram import Router, F, types
from aiogram.filters import Command

from database import get_db_session, is_admin_by_telegram_id, get_all_price_tiers
from models import PriceTier
from .utils import check_admin

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "💰 Price Config")
async def handle_price_config(message: types.Message):
    if not await check_admin(message):
        return

    session = get_db_session()
    try:
        tiers = get_all_price_tiers(session)

        if not tiers:
            msg = "❌ No price tiers configured.\n\nUse `/addprice` to add tiers."
        else:
            msg = "💰 **Price Tiers:**\n\n"
            for tier in tiers:
                msg += f"ID: `{tier.id}` | `{tier.min_ok}-{tier.max_ok}` OK = `{tier.price_per_ok}` per OK\n"

            msg += "\n**Commands:**\n"
            msg += "`/addprice MIN MAX PRICE` - Add tier\n"
            msg += "`/delprice ID` - Delete tier"

        await message.answer(msg, parse_mode='Markdown')
    finally:
        session.close()


@router.message(Command("delprice"))
async def cmd_del_price(message: types.Message):
    """Delete a price tier by ID"""
    session = get_db_session()
    try:
        if not is_admin_by_telegram_id(session, message.from_user.id):
            await message.answer("❌ Admin access required.")
            return

        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("❌ Usage: `/delprice ID`", parse_mode='Markdown')
            return

        try:
            tier_id = int(parts[1])
            tier = session.query(PriceTier).filter_by(id=tier_id).first()

            if tier:
                session.delete(tier)
                session.commit()
                await message.answer(f"✅ Price tier `{tier_id}` deleted successfully.")
            else:
                await message.answer(f"❌ Tier with ID `{tier_id}` not found.")

        except ValueError:
            await message.answer("❌ Invalid ID. Please provide a number.")

    finally:
        session.close()


@router.message(Command("addprice"))
async def cmd_add_price(message: types.Message):
    """Add price tier"""
    session = get_db_session()
    try:
        if not is_admin_by_telegram_id(session, message.from_user.id):
            await message.answer("❌ Admin access required.")
            return

        parts = message.text.split()
        if len(parts) != 4:
            await message.answer(
                "❌ Invalid format.\n"
                "Use: `/addprice MIN MAX PRICE`\n"
                "Example: `/addprice 0 100 2.5`",
                parse_mode='Markdown'
            )
            return

        try:
            min_ok = int(parts[1])
            max_ok = int(parts[2])
            price = float(parts[3])

            new_tier = PriceTier(min_ok=min_ok, max_ok=max_ok, price_per_ok=price)
            session.add(new_tier)
            session.commit()

            await message.answer(
                f"✅ **Price tier added!**\n\n"
                f"`{min_ok}-{max_ok}` OK = `{price}` per OK",
                parse_mode='Markdown'
            )

        except ValueError:
            await message.answer("❌ Invalid numbers.")

    finally:
        session.close()