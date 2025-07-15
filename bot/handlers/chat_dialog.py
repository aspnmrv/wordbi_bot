from telethon import events, Button

from bot.db_tools import _get_current_user_step, _get_user_self_words
from bot.db import (
    get_stat_use_message_db,
    get_event_from_db,
    update_data_events_db,
    get_user_topics_db,
    get_user_level_db,
    get_history_chat_ellie_db,
    update_messages_db,
    increment_counter_and_check
)
from bot.ellie import get_conversations, get_response
from bot.globals import LIMIT_TIME_EVENTS, LIMIT_USES_MESSAGES
from bot.tools import get_keyboard, build_history_message, get_diff_between_ts, is_expected_steps
from bot.bot_instance import bot
from config.config import test_user_id
from bot.decorators import limit_usage


@bot.on(events.NewMessage())
async def dialog_with_ellie(event):
    user_id = event.message.peer_id.user_id
    message_text = event.message.message

    if not await is_expected_steps(user_id, [61, 62]):
        return

    if message_text in ("Quiz me 📝", "Поболтать 💌", "Завершить", "Проверить себя 🧠", "Создать свой набор слов 🧬"):
        return

    if message_text.startswith("/") and await is_expected_steps(user_id, [61, 62]):
        keyboard = await get_keyboard(["Завершить"])
        await event.client.send_message(
            event.chat_id,
            "Чтобы воспользоваться командами из меню, необходимо "
            "закончить диалог с Ellie по кнопке Завершить 🙂",
            reply_to=event.message.id,
            buttons=keyboard
        )
        return

    if not await increment_counter_and_check(user_id, "dialog_with_ellie", 150):
        await event.client.send_message(
            event.chat_id,
            "Ого, какая активность! Но я не успеваю справляться с такой нагрузкой 😔\n\n"
            "Попробуй воспользоваться этой функцией завтра 💜"
        )
        return

    level = await get_user_level_db(user_id)
    words_list = await _get_user_self_words(user_id)
    topics = await get_user_topics_db(user_id)
    keyboard = await get_keyboard(["Завершить"])

    last_ts_quiz = await get_event_from_db(user_id, "message_from_user_quiz")
    last_ts_conv = await get_event_from_db(user_id, "message_from_user_conv")
    quiz_ready = last_ts_quiz is None or await get_diff_between_ts(str(last_ts_quiz)) > LIMIT_TIME_EVENTS
    conv_ready = last_ts_conv is None or await get_diff_between_ts(str(last_ts_conv)) > LIMIT_TIME_EVENTS

    if quiz_ready or conv_ready or user_id == test_user_id:
        cnt_uses = await get_stat_use_message_db(user_id)
        if cnt_uses < LIMIT_USES_MESSAGES or cnt_uses is None or user_id == test_user_id:
            if await is_expected_steps(user_id, [61]):
                await update_messages_db(user_id, "quiz", "user", "ellie", message_text.replace("'", ""))
                await update_data_events_db(user_id, "message_from_user_quiz", {"step": -1})
                history = await get_history_chat_ellie_db(user_id, "quiz") or []
                history = await build_history_message(history)

                async with event.client.action(user_id, "typing"):
                    text = await get_response(user_id, history, message_text, words_list, level)
                if text:
                    await update_messages_db(user_id, "quiz", "ellie", "user", text.replace("'", ""))
                    buttons = [[Button.inline(text="Перевести", data=49)]]
                    await event.client.send_message(event.chat_id, text, reply_to=event.message.id, buttons=buttons)
                    await update_data_events_db(user_id, "message_to_user_quiz", {"step": -1})
                else:
                    await event.client.send_message(
                        event.chat_id,
                        "Что-то сломалось 😣\n\nУже чиним, попробуй позже",
                        buttons=keyboard
                    )
            elif await is_expected_steps(user_id, [62]):
                await update_messages_db(user_id, "conversation", "user", "ellie", message_text)
                await update_data_events_db(user_id, "message_from_user_conv", {"step": -1})
                history = await get_history_chat_ellie_db(user_id, "conversation") or []
                history = await build_history_message(history)

                async with event.client.action(user_id, "typing"):
                    text = await get_conversations(user_id, history, message_text, words_list, topics, level)
                if text:
                    await update_messages_db(user_id, "conversation", "ellie", "user", text.replace("'", ""))
                    buttons = [[Button.inline(text="Перевести", data=49)]]
                    await event.client.send_message(event.chat_id, text, reply_to=event.message.id, buttons=buttons)
                    await update_data_events_db(user_id, "message_to_user_conv", {"step": -1})
                else:
                    await event.client.send_message(
                        event.chat_id,
                        "Что-то сломалось 😣\n\nУже чиним, попробуй позже",
                        buttons=keyboard
                    )
        else:
            await event.client.send_message(
                event.chat_id,
                "Слишком много запросов за сегодня 🙂"
            )
            await update_data_events_db(user_id, "message_from_user_error", {"step": -1, "error": "limit"})
    else:
        await event.client.send_message(
            event.chat_id,
            "Слишком частые запросы!\n\nПопробуй через несколько минут 🙂"
        )
        await update_data_events_db(user_id, "message_from_user_error", {"step": -1, "error": "flood"})
