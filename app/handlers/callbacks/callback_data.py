from aiogram.filters.callback_data import CallbackData

class CreatePostCallback(CallbackData, prefix="create_post"):
  pass
  
class DeletePostCallback(CallbackData, prefix="delete_post"):
  id: int
  
class ViewPostCallback(CallbackData, prefix="view_post"):
  id: int
  
class BackToListCallback(CallbackData, prefix="back_to_list"):
  pass