from aiogram.fsm.state import State, StatesGroup


class CheckinStates(StatesGroup):
    mood = State()
    energy = State()
    stress = State()
    sleep = State()
    note = State()
    tags = State()
