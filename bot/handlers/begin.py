# from telethon import events
#
# from bot.globals import TOPICS
# from bot.tools import get_keyboard, get_proposal_topics, match_topics_name, get_state_markup, is_expected_steps
# from bot.db_tools import (
#     _update_current_user_step,
#     _update_user_states,
#     _get_user_states
# )
# from bot.db import update_data_events_db
# from telethon.tl.custom import Button
# from bot.bot_instance import bot
#
#
# @bot.on(events.NewMessage(pattern="Начать 🚀"))
# async def begin(event):
#     user_id = event.message.peer_id.user_id
#
#     if await is_expected_steps(user_id, [0]):
#         await _update_current_user_step(user_id, 1)
#         total_topics = list(TOPICS.keys())
#
#         await _update_user_states(user_id, "topics", total_topics)
#         await _update_user_states(user_id, "states", ["" for _ in range(len(total_topics))])
#
#         proposal_topics = await match_topics_name(total_topics)
#         markup = event.client.build_reply_markup(await get_proposal_topics(proposal_topics))
#
#         await get_state_markup(markup, user_id)
#
#         await event.client.send_message(
#             event.chat_id,
#             "Выбери темы, которые тебе могут быть интересны 🐥\n\n"
#             "Я буду учитывать их при формировании списка карточек слов для тебя, "
#             "а Ellie AI постарается учесть твои интересы в общении с ней 💜",
#             buttons=markup
#         )
#
#         keyboard = await get_keyboard(["Подтвердить", "Назад"])
#         await event.client.send_message(
#             event.sender_id,
#             "Когда закончишь с выбором, жми на Подтвердить!",
#             buttons=keyboard
#         )
#
#         await update_data_events_db(user_id, "begin", {"step": 1})
#
#     elif await is_expected_steps(user_id, [2]):
#         await _update_current_user_step(user_id, 1)
#
#         current_topics = await _get_user_states(user_id, "topics")
#         current_state = await _get_user_states(user_id, "states")
#         current_topics = await match_topics_name(current_topics)
#
#         markup = event.client.build_reply_markup(await get_proposal_topics(current_topics, current_state))
#         await get_state_markup(markup, user_id)
#
#         await event.client.send_message(
#             event.chat_id,
#             "Выбери темы, которые тебе могут быть интересны 🐥\n\n"
#             "Я буду учитывать их при формировании списка карточек слов для тебя, "
#             "а Ellie AI постарается учесть твои интересы в общении с ней 💜",
#             buttons=markup
#         )
#
#         keyboard = await get_keyboard(["Подтвердить", "Назад"])
#         await event.client.send_message(
#             event.sender_id,
#             "Когда закончишь с выбором, жми на Подтвердить!",
#             buttons=keyboard
#         )
#
#         await update_data_events_db(user_id, "begin", {"step": 2})
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


@bot.on(events.NewMessage(pattern="Начать 🚀"))
async def begin(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [0, 41, 42, 5821]):
        await _update_current_user_step(user_id, 1)
        keyboard = await get_keyboard(["Карточки слов 🧩", "Чат с Ellie ✨", "Назад"])
        text = (
            "Ты можешь выбрать один из двух режимов:\n\n"
            "1️⃣ Карточки слов 🧩: в этом режиме я сформирую для тебя "
            "список слов для изучения на основе "
            "твоих интересов и текущего уровня языка или ты можешь отправить мне "
            "свои интересы, а я сформирую на их основе список слов.\n\n"
            "2️⃣ Чат с Ellie AI ✨: с ней можно сыграть в игру Quiz me или просто поболтать 🙂"
        )

        await event.client.send_message(event.sender_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "choose_level", {"step": step, "level": event.message.message})

        await update_data_events_db(user_id, "begin", {"step": 1})
