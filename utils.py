"""
Utility Functions
"""
import json
import logging
from datetime import datetime, time, timedelta
import base64
from config import DHAKA_TZ, FCM_PROJECT_ID, CREDS_DECRYPT_KEY,ENC_FILE_PATH
from database import get_active_time_config, get_all_price_tiers
import asyncio
import aiohttp
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from Crypto.Cipher import AES

logger = logging.getLogger(__name__)


def get_dhaka_now():
    """Get current time in Dhaka timezone"""
    return datetime.now(DHAKA_TZ)


def get_target_date(session):
    """
    Determines the target date for submission based on the time window.

    Returns:
        tuple: (target_date, is_within_window)
    """
    config = get_active_time_config(session)
    if not config:
        logger.error("No active time configuration found")
        return datetime.now(DHAKA_TZ).date(), False

    now_time = get_dhaka_now().time()
    now_date = get_dhaka_now().date()

    start_time = time(config.start_hour, config.start_minute)
    end_time = time(config.end_hour, config.end_minute)

    is_night_shift = start_time > end_time

    if is_night_shift:
        if now_time >= start_time:
            return now_date + timedelta(days=1), True
        elif now_time <= end_time:
            return now_date, True
        else:
            return now_date, False
    else:
        if start_time <= now_time <= end_time:
            return now_date, True
        else:
            return now_date, False


def calculate_total(ok_count, session):
    """
    Calculate price per OK and total amount based on OK count

    Returns:
        tuple: (price_per_ok, total_amount)
    """
    tiers = get_all_price_tiers(session)

    if not tiers:
        return 0.0, 0.0

    for tier in tiers:
        if tier.min_ok <= ok_count <= tier.max_ok:
            total = ok_count * tier.price_per_ok
            return tier.price_per_ok, total

    return 0.0, 0.0


def format_time_window(config):
    """Format time window for display"""
    if not config:
        return "Not configured"

    return f"{config.start_hour:02d}:{config.start_minute:02d} - {config.end_hour:02d}:{config.end_minute:02d}"


def parse_payment_data(payment_json_str):
    """Parse payment JSON string to dict"""
    if not payment_json_str:
        return {}
    try:
        return json.loads(payment_json_str)
    except:
        return {}


def serialize_payment_data(payment_dict):
    """Serialize payment dict to JSON string"""
    return json.dumps(payment_dict)


def format_payment_info(payment_data):
    """Format payment data for display"""
    if not payment_data:
        return "No payment info"

    lines = []
    for method, number in payment_data.items():
        if number and number != "Not Provided":
            lines.append(f"   {method}: `{number}`")

    return "\n".join(lines) if lines else "No payment info"


import os
import asyncio
import aiohttp
import json
import logging
import base64
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from Crypto.Cipher import AES
from config import FCM_PROJECT_ID,CREDS_DECRYPT_KEY,ENC_FILE_PATH



def get_fcm_access_token_sync():
    """
    Decrypts credentials and returns a fresh FCM access token.
    """
    try:
        if not CREDS_DECRYPT_KEY:
            raise ValueError("CREDS_DECRYPT_KEY not found in environment variables.")

        key = base64.b64decode(CREDS_DECRYPT_KEY)

        if not os.path.exists(ENC_FILE_PATH):
            raise FileNotFoundError(f"{ENC_FILE_PATH} not found.")

        with open(ENC_FILE_PATH, "rb") as f:
            nonce, tag, ciphertext = [ f.read(x) for x in (16, 16, -1) ]

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

        creds_info = json.loads(decrypted_data.decode('utf-8'))

        creds = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/firebase.messaging']
        )
        creds.refresh(Request())
        return creds.token

    except Exception as e:
        logger.error(f"Error getting FCM token: {e}")
        return None

async def get_fcm_access_token():
    """Async wrapper for getting FCM token"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_fcm_access_token_sync)

async def send_fcm_notification(session: aiohttp.ClientSession, device_token: str, title: str, body: str, access_token: str):
    """Sends a single FCM notification"""
    url = f"https://fcm.googleapis.com/v1/projects/{FCM_PROJECT_ID}/messages:send"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "message": {
            "token": device_token.strip(),
            "notification": {
                "title": title,
                "body": body
            },
            "android": {
                "priority": "high"
            }
        }
    }

    try:
        async with session.post(url, headers=headers, json=payload) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error(f"Error sending FCM: {e}")
        return False

async def broadcast_fcm_notifications(device_tokens: list, title: str, body: str):
    """Broadcasts to all tokens with a fresh access token"""
    if not device_tokens:
        return 0

    access_token = await get_fcm_access_token()
    if not access_token:
        logger.error("Failed to retrieve FCM access token")
        return 0

    success_count = 0
    async with aiohttp.ClientSession() as session:
        tasks = []
        for token in device_tokens:
            tasks.append(send_fcm_notification(session, token, title, body, access_token))

        results = await asyncio.gather(*tasks)
        success_count = sum(results)

    return success_count