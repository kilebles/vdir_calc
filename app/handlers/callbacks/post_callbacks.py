import asyncio
from aiogram import Dispatcher, F
from datetime import datetime, time
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from app.database import get_all_posts, add_post, delete_post, get_post_by_id
from app.UI.inline import get_admin_keyboard, get_view_post_keyboard, get_skip_media_keyboard
from app.utils.states import PostCreationState
from app.handlers.callbacks.callback_data import (
  BackToListCallback, CreatePostCallback, DeletePostCallback, SkipMediaCallback, ViewPostCallback
)

#^ Начало создания поста 
async def create_post_callback(callback: CallbackQuery, state: FSMContext):
  await state.set_state(PostCreationState.title)
  await callback.message.edit_text("<b><i>✏ Введите название поста</i></b>", parse_mode="HTML")
  await callback.answer()


#^ Указание названия поста
async def post_title_handler(message: Message, state: FSMContext):
  await state.update_data(title=message.text)
  await state.set_state(PostCreationState.content)
  await message.answer("<b><i>✏ Введите содержимое поста</i></b>", parse_mode="HTML")
  
  
#^ Указания контента поста
async def post_content_handler(message: Message, state: FSMContext):
  await state.update_data(content=message.text)
  await state.set_state(PostCreationState.media)
  await message.answer(
    "<b><i>Добавьте медиаконтент к посту (по желанию, пока заглугшка) ✏</i></b>", 
    reply_markup=get_skip_media_keyboard(),
    parse_mode="HTML"
    )


#^ Указание медиаконтента
async def post_media_handler(message: Message, state: FSMContext):
  media_file_id = None
  
  if message.photo:
    media_file_id = message.photo[-1].file_id
  elif message.video:
    media_file_id = message.video.file_id
  else:
    error_message = await message.answer(
      "<b>💢 Пожалуйста, отправьте фото,\nили пропустите этот шаг</b>", 
      parse_mode="HTML"
    )
    await asyncio.sleep(3)
    await error_message.delete()
    return
  
  await state.update_data(media_content=media_file_id)
  await state.set_state(PostCreationState.schedule_time)
  await message.answer(
    "<b><i>✏ Введите время для рассылки в формате ЧЧ:MM:</i></b>",
    parse_mode="HTML")


#^ Пропуск добавления медиа
async def skip_media_handler(callback: CallbackQuery, state: FSMContext):
  await state.update_data(media_content=None)
  
  await state.set_state(PostCreationState.schedule_time)
  await callback.message.edit_text(
    "<b><i>✏ Введите время для рассылки в формате ЧЧ:MM:</i></b>", 
    parse_mode="HTML"
  )
  await callback.answer()


#^ Указание времени рассылки
async def post_schedule_handler(message: Message, state: FSMContext):
  user_data = await state.get_data()
  
  try:
    schedule_time = datetime.strptime(message.text, "%H:%M").time()
  except ValueError:
    eror_message = await message.answer(
      "<b><i>💢 Неверный формат времени. Укажите в формате <code>ЧЧ:MM</code></i></b>", 
      parse_mode="HTML"
      )
    await asyncio.sleep(3)
    await eror_message.delete()
    #TODO Доделать под МСК
  
  await add_post(
    title=user_data["title"],
    content=user_data["content"],
    media_content=user_data["media_content"],
    schedule_time=schedule_time
  )
  await state.clear()
  
  posts = await get_all_posts()
  keyboard = get_admin_keyboard(posts)
  await message.answer(
    "<b>Вы можете создать новый пост для рассылки,\nили <code>изменить\отключить\удалить</code> существующий 👇🏻</b>",
    reply_markup=keyboard,
    parse_mode="HTML"
    )


#^ Удаление поста
async def delete_post_handler(callback: CallbackQuery, callback_data: DeletePostCallback):
  post_id = callback_data.id
  
  await delete_post(post_id)
  
  posts = await get_all_posts()
  keyboard = get_admin_keyboard(posts)
  
  await callback.message.edit_text(
    text="<b>Вы можете создать новый пост для рассылки,\nили <code>изменить\отключить\удалить</code> существующий 👇🏻</b>",
    reply_markup=keyboard,
    parse_mode="HTML"
  )


#^ Просмотр поста
async def view_post_handler(callback: CallbackQuery, callback_data: ViewPostCallback):
  post_id = callback_data.id
  post = await get_post_by_id(post_id)
  
  if not post:
    await callback.answer("Пост не найден.", show_alert=True)
    return
  
  post_text = (
    f"<b>Время рассылки:</b> <code>{post.schedule_time.strftime('%H:%M')}</code>\n\n"
    f"<b>Название поста:</b> <u><b>{post.title}</b></u>\n"
    f"<b>Текст поста:</b> <i><blockquote expandable>{post.content}</blockquote></i>"
  )
  
  keyboard = get_view_post_keyboard(post_id)
  
  if post.media_content:
    media = InputMediaPhoto(media=post.media_content, caption=post_text, parse_mode="HTML")
    # TODO ДЛЯ ВИДЕО
    # TODO media = InputMediaVideo(media=post.media_content, caption=post_text, parse_mode="HTML")
    await callback.message.edit_media(media=media, reply_markup=keyboard)
  else:
    await callback.message.edit_text(
      text=post_text,
      reply_markup=keyboard,
      parse_mode="HTML"
    )
  
  await callback.answer()
  

#^ Назад к списку постов
async def back_to_list_handler(callback: CallbackQuery, callback_data: BackToListCallback):
  posts = await get_all_posts()
  keyboard = get_admin_keyboard(posts)
  
  try:
    await callback.message.edit_text(
      text="<b>Вы можете создать новый пост для рассылки,\nили <code>изменить\отключить\удалить</code> существующий 👇🏻</b>",
      reply_markup=keyboard,
      parse_mode="HTML"
    )
  except Exception as e:
    await callback.message.delete()
    await callback.message.answer(
      text="<b>Вы можете создать новый пост для рассылки,\nили <code>изменить\отключить\удалить</code> существующий 👇🏻</b>",
      reply_markup=keyboard,
      parse_mode="HTML"
    )
  
  await callback.answer()


#^ Регистрируем все хендлеры 
def register_post_callbacks(dp: Dispatcher):
  dp.callback_query.register(create_post_callback, CreatePostCallback.filter())
  dp.callback_query.register(delete_post_handler, DeletePostCallback.filter())
  dp.callback_query.register(view_post_handler, ViewPostCallback.filter())
  dp.callback_query.register(back_to_list_handler, BackToListCallback.filter())
  dp.callback_query.register(skip_media_handler, SkipMediaCallback.filter())
  dp.message.register(post_title_handler, PostCreationState.title)
  dp.message.register(post_content_handler, PostCreationState.content)
  dp.message.register(post_media_handler, PostCreationState.media)
  dp.message.register(post_schedule_handler, PostCreationState.schedule_time)