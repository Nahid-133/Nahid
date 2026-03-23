from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
from typing import Callable, Awaitable, Any

CHANNEL_USERNAME = "@nahidbscse"

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any]
    ) -> Any:
        bot: Bot = data["bot"]
        user_id = event.from_user.id

        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
            is_subscribed = member.status in [
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR
            ]
        except Exception:
            is_subscribed = False

        if is_subscribed:
            return await handler(event, data)

        join_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
            ]
        ])

        restricted_msg = (
            "🚫 <b>Access Denied!</b>\n\n"
            "👋 Hello! To use this bot's features, you must be a member of our official channel.\n\n"
            "🔹 <b>Step 1:</b> Click the button below to join.\n"
            "🔹 <b>Step 2:</b> Send /start to verify and continue."
        )

        if isinstance(event, Message):
            await event.answer(restricted_msg, parse_mode='HTML', reply_markup=join_keyboard)

        elif isinstance(event, CallbackQuery):
            await event.answer("⚠️ You must join the channel to use this feature!", show_alert=True)

        return None