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
from telethon.tl.types import PeerUser


@bot.on(events.NewMessage(pattern="Подтвердить"))
async def confirmed(event):
    user_id = event.message.peer_id.user_id

    if await is_expected_steps(user_id, [1]):
        step = await _get_current_user_step(user_id)
        await _update_current_user_step(user_id, 2)

        current_topics = await _get_user_states(user_id, "topics")
        current_states = await _get_user_states(user_id, "states")
        chooses_topic = [topic for state, topic in zip(current_states, current_topics) if state != ""]

        if chooses_topic:
            await update_data_topics_db(user_id, chooses_topic)

            topics_msg_id = await _get_user_states(user_id, "topics_msg_id")
            msg_id = int(topics_msg_id.split(",")[0])
            chat_id = int(topics_msg_id.split(",")[1])

            await event.client.edit_message(
                chat_id,
                msg_id,
                text="**Выбранные интересы:**\n\n" + "\n".join(
                    f"▪️ {interest}" for interest in chooses_topic) + "\n\n",
                buttons=None
            )

            keyboard = await get_keyboard([
                "Назад"
            ])
            text = (
                "Обновил настройки 😇"
            )
            await event.client.send_message(event.chat_id, text, buttons=keyboard)

            await update_data_events_db(user_id, "success", {"step": step})
            await _update_user_choose_topic(user_id, sorted(chooses_topic))

        else:
            text = "Не выбрано ни одной темы..🦦"
            keyboard = await get_keyboard(["Подтвердить"])
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "success", {"step": step, "error": "no_topics"})
