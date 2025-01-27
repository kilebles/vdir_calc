from aiogram.fsm.state import State, StatesGroup

class PostCreationState(StatesGroup):
  title = State()
  content = State()
  media = State()
  schedule_time = State()
  
class PostEditState(StatesGroup):
  edit_content = State()
  edit_media = State()
  edit_time = State()