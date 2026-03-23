from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_credentials = State()
    waiting_for_report_file = State()
    waiting_for_export_date = State()
    waiting_for_time_config = State()
    waiting_for_price_tier = State()
    waiting_for_payment_method = State()
    waiting_broadcast_message = State()