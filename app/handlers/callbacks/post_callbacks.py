import asyncio
from aiogram import Router
from datetime import datetime, timedelta
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from app.database import(
  get_all_posts, 
  add_post, 
  Post,
  delete_post, 
  get_post_by_id,
  update_post_time,
  update_post_media, 
  update_post_description, 
  toggle_post_active
) 
from app.UI.inline import get_admin_keyboard, get_view_post_keyboard, get_skip_media_keyboard
from app.utils.states import PostCreationState, PostEditState
from app.handlers.callbacks.callback_data import(
  BackToListCallback, 
  CreatePostCallback, 
  DeletePostCallback, 
  EditDescriptionCallback, 
  EditMediaCallback, 
  EditTimeCallback, 
  SkipMediaCallback, 
  ViewPostCallback, 
  ToggleActiveCallback
)

router = Router()

#region #& Создание постов 
@router.callback_query(CreatePostCallback.filter())
#^ Начало создания поста 
async def create_post_callback(callback: CallbackQuery, state: FSMContext):
  await state.set_state(PostCreationState.title)
  await callback.message.edit_text("<b><i>✏ Введите название поста</i></b>", parse_mode="HTML")
  await callback.answer()


#^ Указание названия поста
@router.message(PostCreationState.title)
async def post_title_handler(message: Message, state: FSMContext):
  await state.update_data(title=message.text)
  await state.set_state(PostCreationState.content)
  await message.answer("<b><i>✏ Введите содержимое поста</i></b>", parse_mode="HTML")
  
  
#^ Указания контента поста
MAX_MESSAGE_LENGTH = 1024
@router.message(PostCreationState.content)
async def post_content_handler(message: Message, state: FSMContext):
  if len(message.text) > MAX_MESSAGE_LENGTH:
    error_message = await message.answer(
      f"❌ Ваш текст слишком длинный! Telegram поддерживает только {MAX_MESSAGE_LENGTH} символов \n"
      f"✏️ Уменьшите длину текста и попробуйте снова",
      parse_mode="HTML"
    )
    await asyncio.sleep(3)
    await error_message.delete()
    return
    
  await state.update_data(content=message.text)
  await state.set_state(PostCreationState.media)
  await message.answer(
    "<b><i>Добавьте <code>фото/видео</code> к посту ✏</i></b>", 
    reply_markup=get_skip_media_keyboard(),
    parse_mode="HTML"
    )


#^ Указание медиаконтента
@router.message(PostCreationState.media)
async def post_media_handler(message: Message, state: FSMContext):
  media_file_id = None
  
  if message.photo:
    media_file_id = message.photo[-1].file_id
  elif message.video:
    media_file_id = message.video.file_id
  else:
    error_message = await message.answer(
      "<b>💢 Пожалуйста, отправьте <code>фото\видео</code>, \nили пропустите этот шаг</b>", 
      parse_mode="HTML"
    )
    await asyncio.sleep(3)
    await error_message.delete()
    return
  
  await state.update_data(media_content=media_file_id)
  await state.set_state(PostCreationState.schedule_time)
  await message.answer(
    "<b><i>✏ Введите время для рассылки в формате ЧЧ:MM по МСК:</i></b>",
    parse_mode="HTML")


#^ Пропуск добавления медиа
@router.callback_query(SkipMediaCallback.filter())
async def skip_media_handler(callback: CallbackQuery, state: FSMContext):
  await state.update_data(media_content=None)
  
  await state.set_state(PostCreationState.schedule_time)
  await callback.message.edit_text(
    "<b><i>✏ Введите время для рассылки в формате ЧЧ:MM по МСК:</i></b>", 
    parse_mode="HTML"
  )
  await callback.answer()


#^ Указание времени рассылки
@router.message(PostCreationState.schedule_time)
async def post_schedule_handler(message: Message, state: FSMContext):
  user_data = await state.get_data()
  
  try:
    user_time = datetime.strptime(message.text, "%H:%M").time()
  except ValueError:
    eror_message = await message.answer(
      "<b><i>💢 Неверный формат времени. Укажите в формате <code>ЧЧ:MM</code> по МСК</i></b>", 
      parse_mode="HTML"
      )
    await asyncio.sleep(3)
    await eror_message.delete()
    return
  
  schedule_time_msk = (datetime.combine(datetime.today(), user_time) + timedelta(hours=2)).time()
  
  await add_post(
    title=user_data["title"],
    content=user_data["content"],
    media_content=user_data["media_content"],
    schedule_time=schedule_time_msk
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
@router.callback_query(DeletePostCallback.filter())
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
@router.callback_query(ViewPostCallback.filter())
async def view_post_handler(callback: CallbackQuery, callback_data: ViewPostCallback):
  post_id = callback_data.id
  post = await get_post_by_id(post_id)
  
  if not post:
    await callback.answer("Пост не найден.", show_alert=True)
    return
  
  post_text = (
    f"<b>Время рассылки МСК:</b> <code>{post.schedule_time.strftime('%H:%M')}</code>\n\n"
    f"<b>Название поста:</b> <u><b>{post.title}</b></u>\n"
    f"<b>Текст поста:</b> <i><blockquote expandable>{post.content}</blockquote></i>"
  )
  
  keyboard = get_view_post_keyboard({
        "id": post.id,
        "title": post.title,
        "is_active": post.is_active,
        "schedule_time": post.schedule_time,
        "content": post.content
    })
  
  if post.media_content:
    if post.media_content.startswith("AgAC"):
      media = InputMediaPhoto(
        media=post.media_content, 
        caption=post_text, 
        parse_mode="HTML"
      )
    else:
      media = InputMediaVideo(
        media=post.media_content, 
        caption=post_text, 
        parse_mode="HTML"
      )
      
    await callback.message.edit_media(media=media, reply_markup=keyboard)
  else:
    await callback.message.edit_text(
      text=post_text,
      reply_markup=keyboard,
      parse_mode="HTML"
    )
  
  await callback.answer()
#endregion




#region #&Настройка постов
#^ Преобразуем объект пост в словарь
def post_to_dict(post:Post) -> dict:
  return {
    "id": post.id,
    "title": post.title,
    "content": post.content,
    "media_content": post.media_content,
    "schedule_time": post.schedule_time,
    "is_active": post.is_active,
  }


#^ Изменение описани
@router.callback_query(EditDescriptionCallback.filter())
async def edit_description_handler(
    callback: CallbackQuery, 
    callback_data: EditDescriptionCallback, 
    state: FSMContext
):
    post_id = callback_data.id
    await state.set_state(PostEditState.edit_content)
    await state.update_data(post_id=post_id)

    try:
        await callback.message.delete()

        await callback.message.answer(
            "<b>✒ Введите новое описание для поста:</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.answer("Ошибка при обработке", show_alert=True)

    await callback.answer()


#^ Обработка нового описания
@router.message(PostEditState.edit_content)
async def update_description_handler(message: Message, state: FSMContext):
  data = await state.get_data()
  post_id = data.get("post_id")

  await update_post_description(post_id, message.text)
  await state.clear()

  post = await get_post_by_id(post_id)
  keyboard = get_view_post_keyboard(post_to_dict(post))

  post_text = (
    f"<b>Время рассылки МСК:</b> <code>{post.schedule_time.strftime('%H:%M')}</code>\n\n"
    f"<b>Название поста:</b> <u><b>{post.title}</b></u>\n"
    f"<b>Текст поста:</b> <i><blockquote expandable>{post.content}</blockquote></i>"
  )

  if post.media_content:
    if post.media_content.startswith("AgAC"):
      await message.answer_photo(
        photo=post.media_content,
        caption=post_text,
        reply_markup=keyboard,
        parse_mode="HTML"
      )
    else:
      await message.answer_video(
        video=post.media_content,
        caption=post_text,
        reply_markup=keyboard,
        parse_mode="HTML"
      )
  else:
    await message.answer(
      text=post_text,
      reply_markup=keyboard,
      parse_mode="HTML"
    )
  

#^ Изменение медиа
@router.callback_query(EditMediaCallback.filter())
async def edit_media_handler(
    callback: CallbackQuery,
    callback_data: EditMediaCallback,
    state: FSMContext
):
    post_id = callback_data.id
    await state.set_state(PostEditState.edit_media)
    await state.update_data(post_id=post_id)

    try:
        await callback.message.delete()
        await callback.message.answer(
            text="<b>🖼️ Отправьте новое фото</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.answer("Ошибка при обновлении сообщения", show_alert=True)

    await callback.answer()
  
  
#^ Обработчик нового медиа
@router.message(PostEditState.edit_media)
async def update_media_handler(message: Message, state: FSMContext):
  data = await state.get_data()
  post_id = data.get("post_id")
  media_file_id = None

  if message.photo:
    media_file_id = message.photo[-1].file_id
  elif message.video:
      media_file_id = message.video.file_id
  else:
    error_message = await message.answer(
      "<b>💢 Пожалуйста, отправьте фото</b>", 
      parse_mode="HTML")
    await asyncio.sleep(3)
    await error_message.delete()
    return

  await update_post_media(post_id, media_file_id)
  await state.clear()

  post = await get_post_by_id(post_id)
  keyboard = get_view_post_keyboard(post_to_dict(post))

  post_text = (
    f"<b>Время рассылки МСК:</b> <code>{post.schedule_time.strftime('%H:%M')}</code>\n\n"
    f"<b>Название поста:</b> <u><b>{post.title}</b></u>\n"
    f"<b>Текст поста:</b> <i><blockquote expandable>{post.content}</blockquote></i>"
  )

  await message.delete()

  if post.media_content.startswith("AgAC"):  # Типа фото
    await message.answer_photo(
      photo=post.media_content,
      caption=post_text,
      reply_markup=keyboard,
      parse_mode="HTML"
    )
  else:
    await message.answer_video(
      video=post.media_content,
      caption=post_text,
      reply_markup=keyboard,
      parse_mode="HTML"
    )


#^ Изменение времени
@router.callback_query(EditTimeCallback.filter())
async def edit_time_handler(
  callback: CallbackQuery, 
  callback_data: EditTimeCallback,
  state: FSMContext
):
  post_id = callback_data.id
  await state.set_state(PostEditState.edit_time)
  await state.update_data(post_id=post_id)
  
  try:
    await callback.message.delete()
    await callback.message.answer(
      text="<b>🕜 Отправьте новое время</b>",
      parse_mode="HTML"
    )
  except Exception as e:
    await callback.answer("Ошибка при обновлении сообщения", show_alert=True)
    
  await callback.answer()


#^ Обработка изменения времени
@router.message(PostEditState.edit_time)
async def update_time_handler(message: Message, state: FSMContext):
  data = await state.get_data()
  post_id = data.get("post_id")
  
  try:
    try:
      new_time = datetime.strptime(message.text, "%H:%M").time()
    except ValueError:
      error_message = await message.answer(
        "<b>💢 Неверный формат времени. Укажите в формате ЧЧ:ММ</b>", 
        parse_mode="HTML"
      )
      await asyncio.sleep(3)
      await error_message.delete()
      return
    
    await update_post_time(post_id, new_time)
    await state.clear()
    
    post = await get_post_by_id(post_id)
    keyboard = get_view_post_keyboard(post_to_dict(post))
    
    post_text = (
            f"<b>Время рассылки МСК:</b> <code>{post.schedule_time.strftime('%H:%M')}</code>\n\n"
            f"<b>Название поста:</b> <u><b>{post.title}</b></u>\n"
            f"<b>Текст поста:</b> <i><blockquote expandable>{post.content}</blockquote></i>"
        )
    
    if post.media_content:
      if post.media_content.startswith("AgAC"):
        await message.answer_photo(
          photo=post.media_content,
          caption=post_text,
          reply_markup=keyboard,
          parse_mode="HTML"
        )
      else:
        await message.answer_video(
          video=post.media_content,
          caption=post_text,
          reply_markup=keyboard,
          parse_mode="HTML"
        )
    else:
      await message.answer(
        text=post_text,
        reply_markup=keyboard,
        parse_mode="HTML"
      )
  except Exception as e:
    error_message = await message.answer(
      "<b>💢 Произошла ошибка при обновлении времени.</b>", 
      parse_mode="HTML"
    )
    await asyncio.sleep(3)
    await error_message.delete()


#^ Назад к списку постов
@router.callback_query(BackToListCallback.filter())
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


#^ Переключение состояния поста
@router.callback_query(ToggleActiveCallback.filter())
async def toggle_active_handler(
  callback: CallbackQuery,
  callback_data: ToggleActiveCallback
):
  post_id = callback_data.id
  post = await get_post_by_id(post_id)
  
  if not post:
    await callback.answer("❗ Пост не найден", show_alert=True)
    return
  
  new_status = not post.is_active
  await toggle_post_active(post_id, new_status)
  
  updated_post = await get_post_by_id(post_id)
  updated_keyboard = get_view_post_keyboard({
    "id": updated_post.id,
    "title": updated_post.title,
    "is_active": updated_post.is_active
  })
  
  await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
  await callback.answer(f"Пост стал {'активным' if new_status else 'неактивным'}")
#endregion