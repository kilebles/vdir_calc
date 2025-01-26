from aiogram.fsm.state import State, StatesGroup

class PostCreationState(StatesGroup):
  title = State()
  content = State()
  media = State()
  schedule_time = State()