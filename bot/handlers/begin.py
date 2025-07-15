from telethon import events

from bot.globals import TOPICS
from bot.tools import get_keyboard, get_proposal_topics, match_topics_name, get_state_markup, is_expected_steps
from bot.db_tools import (
    _update_current_user_step,
    _update_user_states,
    _get_user_states,
    _get_current_user_step
)
from bot.db import update_data_events_db
from telethon.tl.custom import Button
from bot.bot_instance import bot
from bot.decorators import limit_usage


@bot.on(events.NewMessage(pattern="Начать 🚀"))
async def begin(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [0, 41, 42, 5821]):
        await _update_current_user_step(user_id, 1)
        keyboard = await get_keyboard(["Карточки слов 🧩", "Чат с Ellie ✨", "Назад"])
        text = (
            "Ты можешь выбрать один из двух режимов:\n\n"
            "1️⃣ Карточки слов 🧩: отправляй список слов для изучения файлом или просто текстом, и я "
            "создам подборку с карточками, на которой можно тренироваться 🎓\n\n"
            "2️⃣ Чат с Ellie AI ✨: с ней можно поболтать, Ellie AI учтет твой уровень, интересы "
            "и изучаемые слова 🙂"
        )

        await event.client.send_message(event.sender_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "choose_level", {"step": step, "level": event.message.message})

        await update_data_events_db(user_id, "begin", {"step": 1})
