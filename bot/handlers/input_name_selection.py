from telethon import events, Button

from bot.db_tools import _get_current_user_step, _get_user_self_words, _update_current_user_step, _update_user_choose_category

from bot.db import (
    get_stat_use_message_db,
    get_event_from_db,
    update_data_events_db,
    get_user_topics_db,
    get_user_level_db,
    get_history_chat_ellie_db,
    update_messages_db,
    update_user_self_category_words_db,
    get_user_categories_db
)
from bot.ellie import get_conversations, get_response
from bot.globals import LIMIT_TIME_EVENTS, LIMIT_USES_MESSAGES
from bot.tools import get_keyboard, build_history_message, get_diff_between_ts, is_expected_steps
from bot.bot_instance import bot
from config.config import test_user_id


@bot.on(events.NewMessage())
async def dialog_with_ellie(event):
    user_id = event.message.peer_id.user_id
    message_text = event.message.message

    if not await is_expected_steps(user_id, [109]):
        return

    if message_text in ("Quiz me 📝", "Поболтать 💌", "Завершить", "Проверить себя 🧠", "Создать свой набор слов 🧬"):
        return

    if message_text.startswith("/") and await is_expected_steps(user_id, [109]):
        keyboard = await get_keyboard(["Завершить"])
        await event.client.send_message(
            event.chat_id,
            "Чтобы воспользоваться командами из меню, необходимо "
            "закончить создание подборки 🙂",
            reply_to=event.message.id,
            buttons=keyboard
        )
        return

    await _update_current_user_step(user_id, 101)
    keyboard = await get_keyboard(["Увидеть карточки 💜"])

    categories = await get_user_categories_db(user_id)

    if message_text not in categories:
        await update_user_self_category_words_db(user_id=user_id, category=message_text, is_system=False)
        await event.client.send_message(
            event.chat_id,
            f"Подборка '{message_text}' сохранена 💜\nТы всегда можешь вернуться к ней!",
            buttons=keyboard
        )
        await _update_user_choose_category(user_id=user_id, data=message_text, is_system=False)
    else:
        await event.client.send_message(
            event.chat_id,
            f"Подборка с названием '{message_text}' у тебя уже есть. Попробуй придумать другое название 🙃",
            buttons=Button.clear()
        )
        await _update_current_user_step(user_id, 109)
