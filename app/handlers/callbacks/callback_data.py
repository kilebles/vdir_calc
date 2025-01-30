from aiogram.filters.callback_data import CallbackData

class CreatePostCallback(CallbackData, prefix="create_post"):
  pass
  
class DeletePostCallback(CallbackData, prefix="delete_post"):
  id: int
  
class ViewPostCallback(CallbackData, prefix="view_post"):
  id: int
  
class SkipMediaCallback(CallbackData, prefix="skip_media"):
  pass

class EditDescriptionCallback(CallbackData, prefix="edit_description"):
  id: int
  
class EditMediaCallback(CallbackData, prefix="edit_media"):
  id: int

class EditTimeCallback(CallbackData, prefix="edit_time"):
  id: int
  
class ToggleActiveCallback(CallbackData, prefix="toggle_active"):
  id:int
  
class BackToListCallback(CallbackData, prefix="back_to_list"):
  pass

class ContinueStartCallback(CallbackData, prefix="continue"):
  pass

class CalcBuildCallback(CallbackData, prefix="build"):
  pass

class CalcConteinersCallback(CallbackData, prefix="conteiners"):
  pass

class CalcAutoCallback(CallbackData, prefix="calc_auto"):
  pass

class CalcAviaCallback(CallbackData, prefix="calc_avia"):
  pass

class CalcZdCallback(CallbackData, prefix="calc_zd"):
  pass

class CalcBackToMenu(CallbackData, prefix="calc_back"):
  pass

class CalcConfirmCallback(CallbackData, prefix="calc_confirm"):
  pass