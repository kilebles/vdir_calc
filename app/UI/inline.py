from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.handlers.callbacks.callback_data import(
  BackToListCallback, CreatePostCallback, DeletePostCallback, 
  SkipMediaCallback, ViewPostCallback, EditDescriptionCallback,
  EditMediaCallback, EditTimeCallback, ToggleActiveCallback
)


#^ Создание постов (динамическая)
def get_admin_keyboard(posts: list) -> InlineKeyboardMarkup:
  buttons =[]
  
  for post in posts:
    status_icon = "👁" if post['is_active'] else "🔕"
    buttons.append([
      InlineKeyboardButton(
        text=f"{status_icon} {post['title']}", 
        callback_data=ViewPostCallback(id=post['id']).pack(),
      ),
      InlineKeyboardButton(text=f"❌ Удалить", callback_data=DeletePostCallback(id=post['id']).pack())
    ])
    
  buttons.append([InlineKeyboardButton(text="📝 Создать новый пост", callback_data=CreatePostCallback().pack())])
  
  keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
  
  return keyboard


#^ Просмотр постов
def get_view_post_keyboard(post: dict) -> InlineKeyboardMarkup:
  buttons = [
    [
      InlineKeyboardButton(text="✒ Изменить описание", callback_data=EditDescriptionCallback(id=post["id"]).pack()),
      InlineKeyboardButton(text="🖼️ Изменить медиа", callback_data=EditMediaCallback(id=post["id"]).pack())
    ],
    [
      InlineKeyboardButton(text="⏰ Изменить время", callback_data=EditTimeCallback(id=post["id"]).pack()),
      InlineKeyboardButton(
        text="🔕 Сделать неактивным" if post['is_active'] else "🔔 Сделать активным", 
        callback_data=ToggleActiveCallback(id=post['id']).pack()
      )
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