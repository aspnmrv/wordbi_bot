from telethon import events

from bot.tools import get_keyboard, is_expected_steps
from bot.db_tools import (
    _get_current_user_step,
    _update_current_user_step,
    _get_user_states,
    _update_user_choose_topic
)
from bot.db import update_data_topics_db, update_data_events_db
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Подтвердить"))
async def confirmed(event):
    user_id = event.message.peer_id.user_id

    if await is_expected_steps(user_id, [1, 2, 3]):
        step = await _get_current_user_step(user_id)
        await _update_current_user_step(user_id, 2)

        current_topics = await _get_user_states(user_id, "topics")
        current_states = await _get_user_states(user_id, "states")

        chooses_topic = [topic for state, topic in zip(current_states, current_topics) if state != ""]

        if chooses_topic:
            await update_data_topics_db(user_id, chooses_topic)

            keyboard = await get_keyboard([
                "A1-A2: Beginner 💫",
                "B1-B2: Intermediate ⭐️",
                "C1-C2: Advanced 🌟",
                "Назад"
            ])
            text = (
                "Выбери наиболее подходящий для тебя уровень языка 📚\n\n"
                "Это поможет мне сформировать еще более точную персональную подборку слов для тебя 🫶"
            )
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "success", {"step": step})
            await _update_user_choose_topic(user_id, sorted(chooses_topic))

        else:
            text = "Не выбрано ни одной темы..🦦"
            keyboard = await get_keyboard(["Подтвердить"])
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "success", {"step": step, "error": "no_topics"})
