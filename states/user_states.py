from aiogram.fsm.state import State, StatesGroup

class OnboardingState(StatesGroup):
    weight = State()
    height = State()
    age = State()
    gender = State()

class EditMealState(StatesGroup):
    waiting_for_value = State()

class CustomGoalState(StatesGroup):
    waiting_for_goal = State()


class BroadcastState(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()
