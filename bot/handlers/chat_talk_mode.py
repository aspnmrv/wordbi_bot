from telethon import events, Button

from bot.tools import get_keyboard
from bot.db_tools import (
    _get_current_user_step, _update_current_user_step, _get_user_self_words,
    _get_user_test_words, _update_user_words, _update_user_choose_topic
)
from bot.db import (
    get_event_from_db,
    get_stat_use_mode_db,
    get_stat_use_message_db,
    get_stat_use_link_db,
    get_user_topics_db,
    get_user_level_db,
    get_user_words_db,
    update_messages_db,
    update_reviews_db,
    update_data_events_db,
    get_history_chat_ellie_db,
    update_user_words_db
)
from bot.globals import LIMIT_USES, LIMIT_TIME_EVENTS, LIMIT_USES_MESSAGES, LIMIT_LINK_USES, TRANSLATES
from config.config import test_user_id
from bot.ellie import get_conversations, get_response, build_cards_from_text
from bot.tools import build_history_message, build_img_cards, get_diff_between_ts, is_expected_steps
from bot.bot_instance import bot
from bot.decorators import limit_usage


@bot.on(events.NewMessage(pattern="Поболтать 💌"))
@limit_usage("start_conversation_mode", 100)
async def start_conversation_mode(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)
    last_ts_event = await get_event_from_db(user_id, "talking")

    if last_ts_event is None or await get_diff_between_ts(str(last_ts_event)) > LIMIT_TIME_EVENTS:
        cnt_uses = await get_stat_use_mode_db(user_id)
        if cnt_uses < LIMIT_USES or cnt_uses is None or user_id == test_user_id:
            if await is_expected_steps(user_id, [42]):
                await _update_current_user_step(user_id, 62)

                topics = await get_user_topics_db(user_id)
                level = await get_user_level_db(user_id)
                words_list = await _get_user_self_words(user_id)

                async with event.client.action(user_id, "typing"):
                    text = await get_conversations(
                        user_id=user_id,
                        history="",
                        message="",
                        words=words_list,
                        topics=topics,
                        level=level
                    )

                buttons = [
                    [Button.inline("Перевести", data="49")],
                ]
                await event.client.send_message(event.chat_id, text, buttons=buttons, reply_to=event.message.id)
                await event.client.send_message(
                    event.chat_id,
                    "Нажми Завершить, если захочешь закончить 🤗",
                    buttons=await get_keyboard(["Завершить"])
                )
                await update_messages_db(user_id, "conversation", "ellie", "user", text.replace("'", ""))
                await update_data_events_db(user_id, "talking", {"step": step})
        else:
            await event.client.send_message(event.chat_id, "Слишком много запросов за сегодня 🙂")
            await update_data_events_db(user_id, "conversation_error", {"step": -1, "error": "limit"})
    else:
        await event.client.send_message(event.chat_id, "Слишком частые запросы!\n\nПопробуй через несколько минут 🙂")
        await update_data_events_db(user_id, "talking", {"step": step, "error": "flood"})
