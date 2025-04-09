from telethon import events, Button

from db import get_user_for_notify_reviews_db, update_data_events_db
from config.config import test_user_id
from bot_instance import bot


@bot.on(events.NewMessage(pattern="/fiton"))
async def get_fiton(event):
    user_id = event.message.peer_id.user_id

    if user_id == test_user_id:
        chats = await get_user_for_notify_reviews_db()

        if chats:
            text = (
                "Псс..Я заметил, что ты уже пользовался функционалом 💜\n\n. "
                "Напомню, чтобы смотреть свой прогресс по изученным словам, "
                "можно воспользоваться командой /my_stat 💫\n"
            )
            for chat in chats:
                await event.client.send_message(chat, text, buttons=Button.clear())

            await update_data_events_db(user_id, "send_notify_reviews", {"step": -1, "data": chats})
