from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

#^ Создание постов (динамическая)
def get_admin_keyboard(posts: list) -> InlineKeyboardMarkup:
  keyboard = InlineKeyboardMarkup(row_width = 2)
  
  for post in posts:
    keyboard.add(
      InlineKeyboardButton(text=f"📄 {post['title']}", callback_data=f"view_post:{post['id']}"),
      InlineKeyboardButton(text=f"❌ Удалить", callback_data=f"delete_post:{post['id']}")
    )
    
  keyboard.add(InlineKeyboardButton(text="📝 Создать новый пост", callback_data="create_post"))
  
  return keyboard

