from telethon import events, Button

from bot.db_tools import _get_current_user_step, _get_user_test_words, _get_user_self_words, _update_current_user_step
from bot.db import (
    get_user_words_db,
    update_data_events_db,
    update_user_stat_learned_words_db,
    update_user_stat_category_words_db
)
from bot.globals import TRANSLATES
from bot.tools import get_keyboard, is_expected_steps
from bot.handlers.testing_words_command import testing_words
from bot.bot_instance import bot


@bot.on(events.NewMessage())
async def handle_testing_answer(event):
    user_id = event.message.peer_id.user_id
    message_text = event.message.message

    if message_text in (
            "Quiz me 📝",
            "Поболтать 💌",
            "Завершить",
            "Проверить себя 🧠",
            "Создать свой набор слов 🧬"
    ):
        return

    if message_text.startswith("/") and await is_expected_steps(user_id, [61, 62]):
        keyboard = await get_keyboard(["Завершить"])
        await event.client.send_message(
            event.chat_id,
            "Чтобы воспользоваться командами из меню, "
            "необходимо закончить проверку себя по кнопке Завершить 🙂",
            buttons=keyboard,
            reply_to=event.message.id
        )
        return

    keyboard = await get_keyboard(["Завершить"])

    if await is_expected_steps(user_id, [2011]):
        cur_test_word = await _get_user_test_words(user_id)
        user_words = await get_user_words_db(user_id)
        words_test = {en.lower(): ru.lower() for en, ru in zip(user_words[0], user_words[1])}

        if words_test.get(cur_test_word.lower()) == message_text.lower():
            await event.client.send_message(
                event.chat_id,
                "Иии..верно! Так держать 🦾",
                reply_to=event.message.id,
                buttons=keyboard
            )
            await update_data_events_db(
                user_id,
                "testing_success",
                {"step": -1, "word": message_text.lower()}
            )
            await update_user_stat_learned_words_db(user_id, cur_test_word.lower())
            await _update_current_user_step(user_id, 3011)
            await testing_words(event)
        else:
            buttons = [[Button.inline(text="Пропустить", data=56)]]
            await event.client.send_message(
                event.chat_id,
                "Неверно 🙁 попробуй еще раз!",
                reply_to=event.message.id,
                buttons=buttons
            )
            await update_data_events_db(user_id, "testing_failed", {"step": -1, "word": message_text.lower()})

    elif await is_expected_steps(user_id, [2010]):
        cur_test_word = await _get_user_test_words(user_id)
        user_words_en = await _get_user_self_words(user_id)
        user_words_ru = [TRANSLATES[i] for i in user_words_en]
        words_test = {en.lower(): ru.lower() for en, ru in zip(user_words_en, user_words_ru)}

        if words_test.get(cur_test_word.lower()) == message_text.lower():
            await event.client.send_message(
                event.chat_id,
                "Иии..верно! Так держать 🦾",
                reply_to=event.message.id,
                buttons=keyboard
            )
            await update_data_events_db(user_id, "testing_success", {"step": -1, "word": message_text.lower()})
            await update_user_stat_learned_words_db(user_id, cur_test_word.lower())
            await _update_current_user_step(user_id, 3010)
            await testing_words(event)
        else:
            buttons = [[Button.inline(text="Пропустить", data=56)]]
            await event.client.send_message(
                event.chat_id,
                "Неверно 🙁 попробуй еще раз!",
                reply_to=event.message.id,
                buttons=buttons
            )
            await update_data_events_db(user_id, "testing_failed", {"step": -1, "word": message_text.lower()})
