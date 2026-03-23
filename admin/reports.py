"""
Admin Report Handlers
"""
import logging
import io
import asyncio
import pandas as pd
from datetime import datetime
from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InputMediaDocument, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from collections import defaultdict

from database import get_db_session, get_active_payment_methods, get_all_price_tiers
from models import UserAccount, AdminAccount, UserPayment
from .states import AdminStates
from .utils import check_admin, parse_payment_data
from .keyboards import get_admin_keyboard

try:
    from config import REPORT_FOOTER_MSG
except ImportError:
    REPORT_FOOTER_MSG = "📢 **Note:** You can also check from our channel. If you find any fault, please report to admin."

logger = logging.getLogger(__name__)
router = Router()

TELEGRAM_CONCURRENCY_LIMIT = 25
MAX_FILE_SIZE_MB = 50

def escape_markdown(text):
    """
    Escapes special characters for MarkdownV1.
    Characters that need escaping: _ * [ `
    """
    if not text:
        return ""
    text = str(text)
    special_chars = "_*`["
    return "".join(f"\\{char}" if char in special_chars else char for char in text)

def _validate_report_file(filename: str):
    """Validates filename format and returns date or error message."""
    if not filename:
        return None, "File has no name."
    if not filename.endswith('.txt'):
        return None, "Please send a .txt file."
    try:
        date_str = filename.replace('.txt', '')
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return report_date, None
    except ValueError:
        return None, (
            f"Invalid filename format: `{filename}`\n"
            "Expected format: `YYYY-MM-DD.txt`"
        )

def _get_text_stream(lines: list):
    """Creates an in-memory byte stream safely."""
    if not lines:
        return None

    content = "\n".join(lines)
    byte_content = content.encode('utf-8')

    return byte_content

def _generate_csv_stream(csv_data, headers):
    """Generates CSV in-memory."""
    if not csv_data:
        return None
    df = pd.DataFrame(csv_data, columns=headers)
    string_io = io.StringIO()
    df.to_csv(string_io, index=False)
    return io.BytesIO(string_io.getvalue().encode('utf-8'))

async def _send_user_report_safe(bot: Bot, sender_id: int, telegram_username: str, success_list: list, failed_list: list, report_date, total_amount, price_per_ok, payment_data: dict, payment_methods: list, semaphore: asyncio.Semaphore):
    """
    Wrapper that respects the semaphore limit and handles blocked users.
    Sends the FAILED accounts file as a caption in a single message.
    """
    async with semaphore:
        date_str = report_date.strftime('%Y-%m-%d')
        ok_count = len(success_list)
        fail_count = len(failed_list)

        payment_info_lines = []

        if not payment_data:
            payment_data = {}

        if payment_methods:
            for method in payment_methods:
                val = payment_data.get(method.method_name)

                if val and str(val).strip():
                    safe_name = escape_markdown(method.method_name)
                    safe_val = escape_markdown(str(val))
                    payment_info_lines.append(f"   {safe_name}: {safe_val}")

        if payment_info_lines:
            payment_info_str = "\n".join(payment_info_lines)
        else:
            payment_info_str = "   Not Provided"

        safe_username = escape_markdown(telegram_username or 'Unknown')

        user_msg = (
            f"📋 **Daily Status Report**\n\n"
            f"📅 **Date:** `{date_str}`\n"
            f"👤 **User:** {safe_username}\n\n"
            f"✅ **OK Accounts:** `{ok_count}`\n"
            f"❌ **Not OK Accounts:** `{fail_count}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💳 **Payment Info:**\n{payment_info_str}\n\n"
            f"✅ **Status:** Processed. Payment soon!\n\n"
            f"{REPORT_FOOTER_MSG}"
        )

        try:
            if failed_list:
                file_content = _get_text_stream(failed_list)
                file_name = f"{fail_count}_account_failed_{date_str}.txt"
                document = BufferedInputFile(file_content, filename=file_name)

                await bot.send_document(
                    sender_id,
                    document=document,
                    caption=user_msg,
                    parse_mode='Markdown'
                )
            else:
                await bot.send_message(sender_id, user_msg, parse_mode='Markdown')

            return "sent"

        except TelegramForbiddenError:
            logger.warning(f"🚫 User {sender_id} has blocked the bot. Report skipped.")
            return "blocked"

        except TelegramAPIError as e:
            logger.error(f"⚠️ Telegram API Error for {sender_id}: {e}")
            return "error"

        except Exception as e:
            logger.error(f"❌ Unexpected error sending to {sender_id}: {e}")
            return "error"


@router.message(F.text == "📊 Generate Report")
async def handle_generate_report(message: types.Message, state: FSMContext):
    """Handle generate report button"""
    if not await check_admin(message):
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back", callback_data="admin_back")

    await message.answer(
        "📊 **Generate Report**\n\n"
        "Please send a `.txt` file with usernames to check.\n\n"
        "**File name format:** `YYYY-MM-DD.txt`\n"
        "Example: `2026-02-07.txt`",
        parse_mode='Markdown',
        reply_markup=builder.as_markup()
    )
    await state.set_state(AdminStates.waiting_for_report_file)


@router.message(AdminStates.waiting_for_report_file, F.document)
async def process_report_file(message: types.Message, state: FSMContext, bot: Bot):
    """Process report generation - Bulletproof Version with Progress Bar"""

    if message.document.file_size > (MAX_FILE_SIZE_MB * 1024 * 1024):
        await message.answer(f"❌ File is too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB.")
        await state.clear()
        return

    input_stream = io.BytesIO()
    session = get_db_session()

    semaphore = asyncio.Semaphore(TELEGRAM_CONCURRENCY_LIMIT)

    progress_msg = None

    try:
        file_name = message.document.file_name
        if not file_name.endswith('.txt'):
            await message.answer("❌ Invalid file type. Please send a `.txt` file.")
            return

        report_date, error_msg = _validate_report_file(file_name)
        if error_msg:
            await message.answer(f"❌ {error_msg}", parse_mode='Markdown')
            await state.clear()
            return

        status_msg = await message.answer(f"⏳ Processing `{file_name}`...", parse_mode='Markdown')
        file_info = await bot.get_file(message.document.file_id)
        await bot.download_file(file_info.file_path, input_stream)

        input_stream.seek(0)
        content = input_stream.read().decode('utf-8')
        ok_usernames = set(line.strip() for line in content.splitlines() if line.strip())

        if not ok_usernames:
            await message.answer("❌ The file is empty.")
            await state.clear()
            return

        admin_accounts_map = {
            acc.username: acc
            for acc in session.query(AdminAccount).filter_by(entry_date=report_date).all()
        }

        all_user_accounts = session.query(UserAccount).filter_by(entry_date=report_date).all()
        accounts_by_user = defaultdict(list)
        for acc in all_user_accounts:
            accounts_by_user[acc.sender_id].append(acc)

        if not accounts_by_user:
            await message.answer(f"❌ No submissions found for `{report_date}`", parse_mode='Markdown')
            await state.clear()
            return

        payments_db = session.query(UserPayment).filter_by(entry_date=report_date).all()
        payments_map = {p.sender_id: p for p in payments_db}

        price_tiers = get_all_price_tiers(session)

        payment_methods = get_active_payment_methods(session)
        csv_data = []
        bulk_update_mappings = []
        send_tasks = []

        for sender_id, user_accounts in accounts_by_user.items():
            telegram_username = user_accounts[0].telegram_username if user_accounts else "Unknown"
            success_list = []
            failed_list = []

            for acc in user_accounts:
                if acc.username in ok_usernames:
                    success_list.append(acc.username)
                    admin_acc = admin_accounts_map.get(acc.username)
                    if admin_acc:
                        bulk_update_mappings.append({
                            'id': admin_acc.id,
                            'ok_status': True,
                            'sender_id': sender_id,
                            'telegram_username': telegram_username
                        })
                else:
                    failed_list.append(acc.username)

            ok_count = len(success_list)

            total_amount = 0.0
            price_per_ok = 0.0
            if ok_count > 0:
                for tier in price_tiers:
                    if tier.min_ok <= ok_count <= tier.max_ok:
                        price_per_ok = tier.price_per_ok
                        total_amount = ok_count * price_per_ok
                        break

            payment = payments_map.get(sender_id)
            payment_data = parse_payment_data(payment.payment_data if payment else None)
            paid_status = "Yes" if (payment and payment.paid_status) else "No"

            csv_row = [sender_id, telegram_username or "Unknown", ok_count, price_per_ok, total_amount]
            for method in payment_methods:
                csv_row.append(payment_data.get(method.method_name, "Not Provided"))
            csv_row.append(paid_status)
            csv_data.append(csv_row)

            send_tasks.append(
                _send_user_report_safe(
                    bot, sender_id, telegram_username, success_list, failed_list,
                    report_date, total_amount, price_per_ok, payment_data, payment_methods, semaphore
                )
            )

        if bulk_update_mappings:
            session.bulk_update_mappings(AdminAccount, bulk_update_mappings)
        session.commit()


        progress_msg = await message.answer(
            f"📤 **Sending Reports...**\n\n`0 / {len(send_tasks)} users processed.`",
            parse_mode='Markdown'
        )

        results = []
        processed_count = 0
        last_percentage = 0

        for coro in asyncio.as_completed(send_tasks):
            result = await coro
            results.append(result)
            processed_count += 1

            current_percentage = int((processed_count / len(send_tasks)) * 100)

            if current_percentage > last_percentage:
                last_percentage = current_percentage
                try:
                    await progress_msg.edit_text(
                        f"📤 **Sending Reports...**\n\n"
                        f"`{processed_count} / {len(send_tasks)} users processed.` ({current_percentage}%)\n"
                        f"{'█' * (current_percentage // 5)}{'░' * (20 - current_percentage // 5)}",
                        parse_mode='Markdown'
                    )
                except Exception:
                    pass

        sent_count = results.count("sent")
        blocked_count = results.count("blocked")
        error_count = results.count("error")

        headers = ["User ID", "Username", "OK Count", "Rate", "Total Amount"]
        headers.extend([m.method_name for m in payment_methods])
        headers.append("Paid Status")

        csv_stream = _generate_csv_stream(csv_data, headers)
        date_str_file = report_date.strftime('%Y-%m-%d')

        if progress_msg:
            try:
                await progress_msg.delete()
            except Exception:
                pass

        final_msg = (
            f"📊 *Report Complete!*\n\n"
            f"👥 *Total Users:* `{len(accounts_by_user)}`\n"
            f"✅ *Reports Sent:* `{sent_count}`\n"
            f"🚫 *Blocked Users:* `{blocked_count}`\n"
            f"⚠️ *Other Errors:* `{error_count}`"
        )

        await message.answer(final_msg, parse_mode='Markdown')

        if csv_stream:
            await message.answer_document(
                BufferedInputFile(csv_stream.read(), filename=f"{date_str_file}.csv")
            )

    except Exception as e:
        logger.error(f"Critical Error: {e}", exc_info=True)
        await message.answer(f"❌ Critical Error: {str(e)}")
        session.rollback()
    finally:
        session.close()
        await state.clear()
        input_stream.close()

@router.callback_query(F.data == "admin_back")
async def process_back_button(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🛍 **Admin Panel**", parse_mode='Markdown', reply_markup=get_admin_keyboard())
    await callback.answer()