"""
Main Bot Application (With Server Monitoring & FCM Integration)
Optimized for Render Free Tier Deployment
"""
import sys
import asyncio
import logging
import base64
import json
import random
import string
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from middlewares import SubscriptionMiddleware
from config import BOT_TOKEN, PROXY_URL, LOG_FILE, LOG_FORMAT
from database import (
    init_database, get_db_session, close_db_session,
    get_last_server_status, add_server_status, get_all_device_tokens
)
from user import user_router
from admin import admin_router

from utils import broadcast_fcm_notifications
from user.device import router as user_device_router
from admin.broadcast import router as admin_broadcast_router

WEBHOOK_URL = "http://43.173.119.225/api/api/v1/webhook/nRlmI2-8T7x2DAWe1hWxi97qGA1FcCxrNcyCtLTO_Cw/account-push"
TELEGRAM_CHANNEL_ID = "@nahidbscse"
PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

SERVER_ON_MESSAGE = """
🌐<b>INSTAGRAM WORK IS LIVE</b>🌐

📲 <b>𝗜𝗡𝗦𝗧𝗔𝗚𝗥𝗔𝗠 𝗦𝗨𝗕𝗠𝗜𝗧 𝗟𝗜𝗡𝗞</b>
<code>http://43.173.119.225/api/api/v1/webhook/nRlmI2-8T7x2DAWe1hWxi97qGA1FcCxrNcyCtLTO_Cw/account-push</code>

━━━━━━━━━━━━━━━━━━━━━━━
💰 <b>PRICE LIST</b>
━━━━━━━━━━━━━━━━━━━━━━━
🔹 Standard  ➜  <b>*** TK</b>
🔸 300+      ➜  <b>*** TK</b>
💎 1K+       ➜  <b>*** TK</b>

━━━━━━━━━━━━━━━━━━━━━━━
📢 <b>RULES (নিয়মাবলী)</b>
━━━━━━━━━━━━━━━━━━━━━━━
 ১-২টি ফলো দিতে হবে
 পুরাতন আইডি সাবমিট দিবেন না
 খুলেই সাথে সাথে জমা দিন

🤖 <a href='@Nahid_Insta_Detials_bot'>Nahid_Insta_Detials_bot</a>
""".strip()

SERVER_OFF_MESSAGE = """
🚨 <b>SERVER STATUS UPDATE</b>

━━━━━━━━━━━━━━━━━━━━━━━
🔴SERVER IS NOW <b>OFFLINE</b>
━━━━━━━━━━━━━━━━━━━━━━━

We'll notify you when it's back online.

🤖 <a href='@Nahid_Insta_Detials_bot'>Nahid_Insta_Detials_bot</a>
""".strip()

async def check_server_logic(session):
    """
    Checks the server status by sending a dummy payload.
    """
    chars = string.ascii_lowercase + string.digits

    def random_string(length):
        return ''.join(random.choice(chars) for _ in range(length))

    random_user = random_string(8)
    random_pass = random_string(8)
    random_cookie = random_string(10)

    converted_str = f"{random_user}:{random_pass}|||{random_cookie}||"
    encoded_bytes = base64.b64encode(converted_str.encode("utf-8"))
    encoded_str = encoded_bytes.decode("utf-8")
    payload = f"accounts={encoded_str}"

    try:
        async with session.post(
            WEBHOOK_URL,
            headers={'Content-Type': 'text/plain'},
            data=payload,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            text_data = await response.text()
            if response.status == 200 and text_data:
                try:
                    decoded = json.loads(text_data)
                    if isinstance(decoded, list) and len(decoded) > 0:
                        decoded = decoded[0]

                    data_node = decoded.get('data') if isinstance(decoded, dict) else decoded
                    if not isinstance(data_node, dict):
                        data_node = decoded

                    success_count = data_node.get('success_count', 0)
                    failed_count = data_node.get('failed_count', 0)

                    if failed_count > 0 or success_count > 0:
                        return "ON"
                    return "OFF"
                except json.JSONDecodeError:
                    return "OFF"
            return "OFF"
    except Exception as e:
        logger.error(f"Error checking server: {e}")
        return "OFF"


async def monitor_job(bot: Bot):
    """
    Scheduled task: Checks status, saves to DB, and alerts if changed.
    """
    logger.info("Running scheduled server check...")

    async with aiohttp.ClientSession() as session:
        current_status = await check_server_logic(session)

    db_session = get_db_session()
    try:
        last_record = get_last_server_status(db_session)
        last_status = last_record.status if last_record else None

        logger.info(f"Monitor -> Last: {last_status} | Current: {current_status}")

        if last_status is None:
            add_server_status(db_session, current_status)
            return

        if last_status != current_status:
            add_server_status(db_session, current_status)

            msg = SERVER_ON_MESSAGE if current_status == "ON" else SERVER_OFF_MESSAGE
            try:
                await bot.send_message(
                    TELEGRAM_CHANNEL_ID,
                    msg,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Telegram notify error: {e}")

            try:
                tokens = get_all_device_tokens(db_session)
                if tokens:
                    title = "✅ SERVER ONLINE" if current_status == "ON" else "❌ SERVER OFFLINE"
                    body = "Instagram work is LIVE!" if current_status == "ON" else "Instagram work OFF"

                    asyncio.create_task(broadcast_fcm_notifications(tokens, title, body))
                    logger.info(f"FCM Broadcast initiated for {len(tokens)} devices.")
            except Exception as e:
                logger.error(f"FCM Broadcast error: {e}")

    except Exception as e:
        logger.error(f"Database error: {e}")
        db_session.rollback()
    finally:
        close_db_session(db_session)


async def health_check(request):
    """Lightweight health check for Render"""
    return web.json_response({
        "status": "healthy",
        "service": "instagram-monitor-bot"
    })


async def root_handler(request):
    """Root endpoint"""
    return web.Response(
        text="✅ Bot is active and monitoring Instagram server status.",
        content_type="text/html"
    )


async def start_web_server():
    """
    Start web server for Render health checks.
    This MUST start quickly and bind to PORT.
    """
    app = web.Application()

    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_check)

    runner = web.AppRunner(app)
    await runner.setup()

    PORT=10000
    site = web.TCPSite(runner, host='0.0.0.0', port=PORT)
    await site.start()

    logger.info(f"🌐 Web server started on port {PORT}")
    return runner


async def init_bot():
    """
    Initialize bot and dispatcher.
    Separated from main to handle startup gracefully.
    """
    if PROXY_URL:
        connector = aiohttp.ProxyConnector.from_url(PROXY_URL)
        bot = Bot(token=BOT_TOKEN, connector=connector)
    else:
        bot = Bot(token=BOT_TOKEN)

    dp = Dispatcher(storage=MemoryStorage())

    user_router.message.middleware(SubscriptionMiddleware())

    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(user_device_router)
    dp.include_router(admin_broadcast_router)

    return bot, dp


async def main():
    """
    Main entry point.
    CRITICAL: Start web server FIRST (within 15 min timeout),
    then start bot polling.
    """
    init_database()

    web_runner = await start_web_server()

    bot, dp = await init_bot()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        monitor_job,
        IntervalTrigger(seconds=30),
        args=[bot],
        id='server_monitor',
        replace_existing=True
    )
    scheduler.start()

    logger.info("✅ System Started: Web server up, monitoring @ 30s intervals")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        raise
    finally:
        scheduler.shutdown()
        await web_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot Stopped.")
