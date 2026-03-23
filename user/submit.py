import json
import logging
import os
import base64
from aiogram import Router, types, F
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from models import UserAccount, UserPayment, AdminAccount
from database import get_db_session
from utils import get_target_date

logger = logging.getLogger(__name__)
router = Router()


class SecurityModule:
    INTERNAL_SALT = "SKYSYS_PRO_SALT_99821_Bokachondro985"
    ITERATIONS = 2000
    KEY_LENGTH = 32

    @staticmethod
    def _derive_key(password: str) -> bytes:
        return PBKDF2(
            password,
            SecurityModule.INTERNAL_SALT.encode('utf-8'),
            dkLen=SecurityModule.KEY_LENGTH,
            count=SecurityModule.ITERATIONS,
            hmac_hash_module=SHA256
        )

    @staticmethod
    def unpack(packed_data: str, password: str) -> str:
        """
        Decrypts data packed by Flutter SecureVault.pack()
        Format: Base64( UTF8( IV_Base64 : Encrypted_Base64 ) )
        """
        try:
            combined_decoded = base64.b64decode(packed_data).decode('utf-8')

            parts = combined_decoded.split(':')
            if len(parts) != 2:
                return None

            iv_b64, cipher_b64 = parts

            iv = base64.b64decode(iv_b64)
            cipher_bytes = base64.b64decode(cipher_b64)

            key = SecurityModule._derive_key(password)

            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            decrypted_bytes = cipher.decrypt_and_verify(
                cipher_bytes[:-16],
                cipher_bytes[-16:]
            )

            return decrypted_bytes.decode('utf-8')

        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Decryption failed: {e}")
            return None


def _parse_file_content(file_content: str):
    """
    Parse file format:
      Line 1 → password
      Line 2 → encrypted JSON data
    Returns (password, encrypted_data) or (None, None) on failure.
    """
    newline_idx = file_content.find('\n')
    if newline_idx == -1:
        return None, None

    password = file_content[:newline_idx].strip()
    encrypted_data = file_content[newline_idx + 1:].strip()

    if not password or not encrypted_data:
        return None, None

    return password, encrypted_data



@router.message(F.text == "📁 Submit Files")
async def handle_submit_files_button(message: types.Message):
    """Handle submit files button"""
    session = get_db_session()
    try:
        target_date, is_valid = get_target_date(session)

        if not is_valid:
            await message.answer(
                "⏰ **Submission Window Closed**\n\n"
                "You can only submit files during the active submission window.\n"
                "Please check the manual for submission times.",
                parse_mode='Markdown'
            )
            return

        await message.answer(
            "📤 **Ready to Receive Files**\n\n"
            f"📅 Target Date: `{target_date.strftime('%Y-%m-%d')}`\n\n"
            "Please send your **Encrypted JSON** file exported from the latest Secure App.\n\n"
            "⚠️ **Important:**\n"
            "1. File must be exported from the **latest version** of the Secure App.\n",
            parse_mode='Markdown'
        )

    finally:
        session.close()


@router.message(F.document, lambda msg: msg.document.file_name.endswith('.json'))
async def handle_json_files(message: types.Message):
    """Handle JSON file uploads (Strictly Encrypted Only)"""

    file_name = message.document.file_name
    if not file_name.endswith('.json'):
        return

    session = get_db_session()
    temp_path = None

    try:
        bot = message.bot
        target_date, is_valid_window = get_target_date(session)

        if not is_valid_window:
            await message.reply("⏰ Submission window is closed.")
            return

        file_info = await bot.get_file(message.document.file_id)
        temp_path = f"/tmp/temp_{message.document.file_id}.json"
        await bot.download_file(file_info.file_path, temp_path)

        with open(temp_path, 'r') as f:
            file_content = f.read()

        try:
            json.loads(file_content)
            await message.reply(
                "🚫 **Security Error: Plain Text Rejected**\n\n"
                "You uploaded a normal JSON file. This bot only accepts **Encrypted** files.\n\n"
                "📌 Please update your app to the latest version and export the file again.",
                parse_mode='Markdown'
            )
            return
        except json.JSONDecodeError:
            pass

        password, encrypted_data = _parse_file_content(file_content)

        if not password or not encrypted_data:
            await message.reply(
                "🔐 **Invalid File Format**\n\n"
                "Could not read password or encrypted data from the file.\n"
                "Please make sure you are using the **latest version** of the app.",
                parse_mode='Markdown'
            )
            return

        decrypted_str = SecurityModule.unpack(encrypted_data, password)

        if not decrypted_str:
            await message.reply(
                "❌ **Decryption Failed**\n\n"
                "The file could not be decrypted. It may be corrupted or from an incompatible app version.",
                parse_mode='Markdown'
            )
            return

        try:
            data = json.loads(decrypted_str)
        except json.JSONDecodeError:
            await message.reply("❌ Decrypted data is not valid JSON.")
            return

        full_username = message.from_user.username or "no_username"
        sender_id = message.from_user.id

        original_accounts = data if isinstance(data, list) else [data]

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
            session.commit()

        cleaned_accounts = []
        seen_internal = set()

        internal_file_dupe_count = 0
        db_duplicate_count = 0
        conflict_removals = 0
        new_accounts_count = 0

        for acc in original_accounts:
            if not isinstance(acc, dict):
                continue

            username = acc.get('username')
            acc_password = acc.get('password', '')

            if not username:
                continue

            if username in seen_internal:
                internal_file_dupe_count += 1
                continue

            seen_internal.add(username)

            admin_entry = session.query(AdminAccount).filter_by(
                username=username,
                entry_date=target_date
            ).first()

            if admin_entry:
                user_entry = session.query(UserAccount).filter_by(
                    username=username,
                    entry_date=target_date
                ).first()

                if user_entry:
                    if user_entry.sender_id == sender_id:
                        db_duplicate_count += 1
                    else:
                        session.delete(user_entry)
                        conflict_removals += 1
                else:
                    conflict_removals += 1

            else:
                new_admin_acc = AdminAccount(
                    username=username,
                    password=acc_password,
                    entry_date=target_date
                )
                session.add(new_admin_acc)

                new_user_acc = UserAccount(
                    username=username,
                    password=acc_password,
                    sender_id=sender_id,
                    entry_date=target_date,
                    telegram_username=full_username
                )
                session.add(new_user_acc)

                new_accounts_count += 1
                cleaned_accounts.append(acc)

        session.commit()

        total_duplicates = internal_file_dupe_count + db_duplicate_count

        response_msg = (
            f"⚡ **Account Processing Complete** ⚡\n\n"
            f"👤 **User:** `{full_username}`\n"
            f"📅 **Date:** `{target_date.strftime('%Y-%m-%d')}`\n"
            f"📥 **File Received:** `{len(original_accounts)}` accounts\n"
            f"🔁 **Duplicates (File + Same User):** `{total_duplicates}`\n"
            f"🚫 **Conflicts (Removed/Skipped):** `{conflict_removals}`\n"
            f"✅ **New Accounts Added:** `{new_accounts_count}`\n\n"
            f"⚠️ **Info:**\n"
            f"- *Duplicates:* You already submitted these.\n"
            f"- *Conflicts:* Removed from previous users and ignored for you."
        )

        await message.reply(response_msg, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        session.rollback()
        await message.reply("❌ Error processing file.")
    finally:
        session.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)