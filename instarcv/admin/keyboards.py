from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_admin_keyboard():
    """Generate admin keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Generate Report"), KeyboardButton(text="📤 Export Data")],
            [KeyboardButton(text="⏰ Time Config"), KeyboardButton(text="💰 Price Config")],
            [KeyboardButton(text="💳 Payment Methods"), KeyboardButton(text="👤 User Stats")],
            [KeyboardButton(text="📢 Broadcast")]
        ],
        resize_keyboard=True
    )
    return keyboard