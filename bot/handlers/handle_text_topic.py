import ast

from telethon import events
from telethon import events, Button
from bot.bot_instance import bot
from bot.handlers.common import (
    finalize_cards_and_send_next_steps
)
from bot.tools import get_keyboard, build_img_cards, is_expected_steps, is_valid_word_list, is_simple_word_list
from bot.db import (
    get_user_level_db, update_user_words_db, update_data_events_db,
    update_user_stat_category_words_db
)
from bot.ellie import build_cards_from_text
from bot.decorators import limit_usage


@bot.on(events.NewMessage())
@limit_usage("handle_custom_topic_input", 15)
async def handle_custom_topic_input(event):
    user_id = event.message.peer_id.user_id
    message_text = event.message.message

    if not await is_expected_steps(user_id, [52]):
        return

    if message_text in ("Quiz me 📝", "Поболтать 💌", "Завершить", "Проверить себя 🧠", "Создать свой набор слов 🧬"):
        return

    if event.message.file:
        return

    if await is_valid_word_list(message_text) or await is_simple_word_list(message_text):
        return

    await event.client.send_message(event.chat_id, "Формирую список слов...", buttons=Button.clear())

    level = await get_user_level_db(user_id)
    try:
        card_words = await build_cards_from_text(message_text, level, user_id)

        if not card_words or card_words == "None":
            keyboard = await get_keyboard(["Завершить"])
            await event.client.send_message(
                event.chat_id,
                "Кажется, выбранные темы слишком специфичны 😔\n\nПопробуй выбрать другие темы 💜",
                buttons=keyboard
            )
            await update_data_events_db(user_id, "cards_from_link_error", {"step": -1, "error": "specific"})
            return

        card_words = ast.literal_eval(card_words)
        if not isinstance(card_words, dict):
            keyboard = await get_keyboard(["Завершить"])
            await event.client.send_message(
                event.chat_id,
                "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜",
                buttons=keyboard
            )
            await update_data_events_db(user_id, "cards_from_link_error", {"step": -1, "error": "api"})
            return

        await finalize_cards_and_send_next_steps(event, user_id, card_words, "tmp349201", next_step=109)

    except Exception as e:
        keyboard = await get_keyboard(["Завершить"])
        await event.client.send_message(
            event.chat_id,
            "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜",
            buttons=keyboard
        )
        await update_data_events_db(user_id, "cards_from_link_error", {"step": -1, "error": str(e)})
