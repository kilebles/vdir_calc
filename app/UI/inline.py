from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.handlers.callbacks.callback_data import CreatePostCallback

#^ Создание постов (динамическая)
def get_admin_keyboard(posts: list) -> InlineKeyboardMarkup:
  buttons =[]
  
  for post in posts:
    buttons.append([
      InlineKeyboardButton(text=f"📄 {post['title']}", callback_data=f"view_post:{post['id']}"),
      InlineKeyboardButton(text=f"❌ Удалить", callback_data=f"delete_post:{post['id']}")
    ])
    
  buttons.append([
    InlineKeyboardButton(
      text="📝 Создать новый пост", 
      callback_data=CreatePostCallback().pack()
      )
    ])
  
  keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
  
  return keyboard

