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
  
class FreightCalculationState(StatesGroup):
  choosing_delivery_type = State()
  entering_origin_city = State()
  entering_destination_city = State()
  entering_weight = State()
  entering_volume = State()
  confirming_data = State()
