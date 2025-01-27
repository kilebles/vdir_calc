from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.handlers.callbacks.callback_data import (
  BackToListCallback, CreatePostCallback, DeletePostCallback, SkipMediaCallback, ViewPostCallback)


#^ Создание постов (динамическая)
def get_admin_keyboard(posts: list) -> InlineKeyboardMarkup:
  buttons =[]
  
  for post in posts:
    buttons.append([
      InlineKeyboardButton(text=f"📄 {post['title']}", callback_data=ViewPostCallback(id=post['id']).pack()),
      InlineKeyboardButton(text=f"❌ Удалить", callback_data=DeletePostCallback(id=post['id']).pack())
    ])
    
  buttons.append([InlineKeyboardButton(text="📝 Создать новый пост", callback_data=CreatePostCallback().pack())])
  
  keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
  
  return keyboard


#^ Просмотр постов
def get_view_post_keyboard(post_id: int) -> InlineKeyboardMarkup:
  buttons = [
    [
      InlineKeyboardButton(text="✒ Изменить описание", callback_data=f"edit_description:{post_id}"),
      InlineKeyboardButton(text="🖼️ Изменить медиа", callback_data=f"edit_media:{post_id}")
    ],
    [
      InlineKeyboardButton(text="⏰ Изменить время", callback_data=f"edit_time:{post_id}"),
      InlineKeyboardButton(text="🔕 Сделать неактивным", callback_data=f"deactivate_post:{post_id}")
    ],
    [InlineKeyboardButton(text="↩ Назад", callback_data=BackToListCallback().pack())]
  ]
  
  keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
  
  return keyboard


#^ Пропуск шага с добавлением медиаконтента
def get_skip_media_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏭️ Пропустить",
                callback_data=SkipMediaCallback().pack()
            )
        ]
    ])