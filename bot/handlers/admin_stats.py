from telethon import events, Button
from bot.db import get_private_db, update_data_events_db
from config.config import test_user_id
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="/deloss"))
async def get_delos(event):
    user_id = event.message.peer_id.user_id

    if user_id == test_user_id:
        data = await get_private_db()

        if data:
            total_users, users_ellie, users_cards, users_reviews = data
            text = (
                "Приветики\n\nОсновная статистика: \n\n"
                f"Всего пользователей: {total_users}\n"
                f"Воспользовались чатом: {users_ellie}\n"
                f"Воспользовались карточками: {users_cards}\n"
                f"Оставили отзыв: {users_reviews}\n\n<3"
            )
            await event.client.send_message(event.chat_id, text, buttons=Button.clear())
            await update_data_events_db(user_id, "download_stats", {"step": -1, "data": data})
