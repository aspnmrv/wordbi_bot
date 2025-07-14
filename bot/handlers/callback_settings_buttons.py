from telethon import events, Button
from bot.db_tools import (
    _get_current_user_step,
    _update_current_user_step,
    _update_user_choose_category,
    _get_user_choose_category,
    _update_user_self_words,
    _update_user_states,
    _get_user_states
)
from bot.db import (
    get_user_words_db,
    get_user_categories_db,
    get_user_words_by_category_db,
    update_data_events_db
)
from bot.tools import (
    get_keyboard,
    build_img_cards,
    is_expected_steps,
    match_topics_name,
    get_proposal_topics,
    get_state_markup
)
from bot.handlers.cards_by_interest import get_start_cards
from bot.globals import TOPICS
from bot.bot_instance import bot


@bot.on(events.CallbackQuery(pattern=r"^(profile_int|profile_lev)"))
async def handle_get_cards_callback(event):
    user_id = event.original_update.user_id
    if not await is_expected_steps(user_id, [5821]):
        return

    data_filter = event.data.decode("utf-8")
    await _update_current_user_step(user_id, 1)

    if data_filter == "profile_int":
        await event.edit(
            "Открываю твои интересы 🐥...",
            buttons=None
        )
        current_topics = await _get_user_states(user_id, "topics")
        await _update_current_user_step(user_id, 1)

        if not current_topics:
            total_topics = list(TOPICS.keys())
            await _update_user_states(user_id, "topics", total_topics)
            await _update_user_states(user_id, "states", ["" for _ in range(len(total_topics))])

            proposal_topics = await match_topics_name(total_topics)
            markup = event.client.build_reply_markup(await get_proposal_topics(proposal_topics))
            await get_state_markup(markup, user_id)

            # await update_data_events_db(user_id, "begin", {"step": 1})
        else:

            current_topics = await _get_user_states(user_id, "topics")
            current_state = await _get_user_states(user_id, "states")
            current_topics = await match_topics_name(current_topics)

            markup = event.client.build_reply_markup(await get_proposal_topics(current_topics, current_state))
            await get_state_markup(markup, user_id)

        msg = await event.client.send_message(
            event.chat_id,
            "Выбери темы, которые тебе могут быть интересны 🐥\n\n"
            "Я буду учитывать их при формировании списка карточек слов для тебя, "
            "а Ellie AI постарается учесть твои интересы в общении с ней 💜",
            buttons=markup
        )
        await _update_user_states(user_id, "topics_msg_id", str(msg.id) + "," + str(event.chat_id))

        keyboard = await get_keyboard(["Подтвердить"])
        await event.client.send_message(
            event.sender_id,
            "Когда закончишь с выбором, жми на Подтвердить!",
            buttons=keyboard
        )
        await _update_current_user_step(user_id, 1)

    elif data_filter == "profile_lev":
        await event.edit(
            "⏳",
            buttons=None
        )
        keyboard = await get_keyboard([
            "A1-A2: Beginner 💫",
            "B1-B2: Intermediate ⭐️",
            "C1-C2: Advanced 🌟"
        ])
        text = (
            "Выбери наиболее подходящий для тебя уровень языка 📚\n\n"
            "Это поможет мне сформировать еще более точную персональную подборку слов для тебя 🫶"
        )
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await _update_current_user_step(user_id, 392)
