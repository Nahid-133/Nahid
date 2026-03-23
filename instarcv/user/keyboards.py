"""
User Keyboards
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton , InlineKeyboardButton ,InlineKeyboardMarkup

def get_user_keyboard():
    """Generate user main keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Submit Files"), KeyboardButton(text="📊 My Reports")],
            [KeyboardButton(text="💰 Payment Methods"), KeyboardButton(text="📖 Manual")],
            [KeyboardButton(text="📱 Set Device")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_device_management_keyboard():
    """Keyboard for choosing to update device token"""
    buttons = [
        [
            InlineKeyboardButton(text="🔄 Replace Token", callback_data="replace_device_token"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_device_update")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)