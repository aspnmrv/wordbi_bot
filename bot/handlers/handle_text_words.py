import ast

from telethon import events
from telethon import events, Button
from bot_instance import bot
from handlers.common import (
    finalize_cards_and_send_next_steps,
    send_error_message
)
from tools import (
    get_keyboard,
    build_img_cards,
    is_expected_steps,
    is_valid_word_list,
    is_simple_word_list,
    parse_word_list
)
from db import (
    get_user_level_db, update_user_words_db, update_data_events_db,
    update_user_stat_category_words_db
)
from ellie import get_cards_from_simple_list


@bot.on(events.NewMessage())
async def handle_custom_topic_input(event):
    user_id = event.message.peer_id.user_id
    message_text = event.message.message

    if not await is_expected_steps(user_id, [52]):
        return

    if message_text in ("Quiz me 📝", "Поболтать 💌", "Завершить", "Проверить себя 🧠", "Создать свой набор слов 🧬"):
        return

    if event.message.file:
        return

    if not await is_valid_word_list(message_text) and not await is_simple_word_list(message_text):
        return

    await event.client.send_message(event.chat_id, "Формирую список слов...", buttons=Button.clear())

    level = await get_user_level_db(user_id)
    try:
        if await is_valid_word_list(message_text):
            card_words = await parse_word_list(message_text)

            if not card_words:
                keyboard = await get_keyboard(["Завершить"])
                await event.client.send_message(
                    event.chat_id,
                    "Не получилось составить карточки 😔\n\nПопробуй еще раз 💜",
                    buttons=keyboard
                )
                await update_data_events_db(user_id, "cards_from_text_error", {"step": -1, "error": "wrong_format"})
                return

            if not isinstance(card_words, dict):
                keyboard = await get_keyboard(["Завершить"])
                await event.client.send_message(
                    event.chat_id,
                    "Не получилось составить карточки 😔\n\nПопробуй еще раз 💜",
                    buttons=keyboard
                )
                await update_data_events_db(user_id, "cards_from_text_error", {"step": -1, "error": "wrong_format"})
                return

            await send_error_message(user_id, event, card_words)
            await finalize_cards_and_send_next_steps(event, user_id, card_words, message_text, next_step=101)
        elif await is_simple_word_list(message_text):
            card_words = await get_cards_from_simple_list(user_id, message_text)
            if not card_words:
                keyboard = await get_keyboard(["Завершить"])
                await event.client.send_message(
                    event.chat_id,
                    "Кажется, выбранные темы слишком специфичны 😔\n\nПопробуй выбрать другие темы 💜",
                    buttons=keyboard
                )
                await update_data_events_db(user_id, "cards_from_list_error", {"step": -1, "error": "specific"})
                return

            card_words = ast.literal_eval(card_words)
            print("card_words", card_words)

            if not isinstance(card_words, dict):
                print("if not isinstance(card_words, dict):")
                keyboard = await get_keyboard(["Завершить"])
                await event.client.send_message(
                    event.chat_id,
                    "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜",
                    buttons=keyboard
                )
                await update_data_events_db(user_id, "cards_from_list_error", {"step": -1, "error": "api"})
                return

            await send_error_message(user_id, event, card_words)
            await finalize_cards_and_send_next_steps(event, user_id, card_words, message_text, next_step=101)

    except Exception as e:
        keyboard = await get_keyboard(["Завершить"])
        await event.client.send_message(
            event.chat_id,
            "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜",
            buttons=keyboard
        )
        await update_data_events_db(user_id, "cards_from_list_error", {"step": -1, "error": str(e)})
