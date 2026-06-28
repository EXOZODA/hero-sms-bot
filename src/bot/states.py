from aiogram.fsm.state import StatesGroup, State


class RentStates(StatesGroup):
    """FSM состояния для процесса аренды номера."""
    choosing_service = State()
    choosing_country = State()
    choosing_rent_type = State()
    choosing_duration = State()
    confirming = State()
    waiting_for_sms = State()


class TopUpStates(StatesGroup):
    """FSM состояния для пополнения баланса."""
    waiting_for_amount = State()
