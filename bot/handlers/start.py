from telethon import events

from tools import get_keyboard
from db_tools import _update_current_user_step, _create_db
from db import is_user_exist_db, update_data_users_db, update_data_events_db
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    print(event)
    sender_info = await event.get_sender()
    user_id = event.message.peer_id.user_id
    await _create_db()
    await _update_current_user_step(user_id, 0)
    if not await is_user_exist_db(user_id):
        await update_data_users_db(sender_info)

    keyboard = await get_keyboard(["Начать 🚀", "Обо мне 👾"])
    text = (
        "Hi! 👋\n\nРад, что тебе интересно изучение английского языка! "
        "С Wordbi ты сможешь качественно расширить свой vocabulary. \n\n"
        "Хороший объем словарного запаса поможет читать книги, смотреть любимые фильмы в оригинале и "
        "более эффективно и уверенно использовать язык в жизни 😉"
    )
    await event.client.send_message(event.chat_id, text, buttons=keyboard)
    await update_data_events_db(user_id, "start", {"step": 0})
