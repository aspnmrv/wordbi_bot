from telethon import events, Button

from db_tools import _get_current_user_step, _update_current_user_step
from db import update_data_events_db, get_user_level_db, get_user_topics_db
from tools import get_keyboard, is_expected_steps, get_code_fill_form
from handlers.begin import begin
from bot_instance import bot


@bot.on(events.NewMessage(pattern="/interests"))
async def change_interests(event):
    user_id = event.message.peer_id.user_id
    if not await is_expected_steps(user_id, [3011, 3010, 2011, 2010, 61, 62]):
        step = await _get_current_user_step(user_id)
        await update_data_events_db(user_id, "change_interests", {"step": step})
        code = await get_code_fill_form(user_id)
        if code == -1:
            await event.client.send_message(
                event.chat_id,
                "Еще не выбраны настройки ☺️\n\nНажимай на /start",
                buttons=Button.clear()
            )
            await update_data_events_db(user_id, "change_interests", {"step": -1, "error": "without users"})
        elif code == -2:
            await update_data_events_db(user_id, "change_interests", {"step": -1, "error": "without_interests"})
            await event.client.send_message(event.chat_id, "Еще не выбраны интересы. Сделаем это прямо сейчас? ☺️")
            await _update_current_user_step(user_id, 0)
            await begin(event)
        else:
            await _update_current_user_step(user_id, 2)
            await begin(event)
