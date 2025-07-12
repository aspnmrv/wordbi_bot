from telethon import events
from bot_instance import bot
from handlers.common import (
    finalize_cards_and_send_next_steps,
    send_error_message
)
from tools import get_keyboard, is_expected_steps, extract_text_from_docx
from db import update_data_events_db
from ellie import parse_file
import ast
import os


@bot.on(events.NewMessage())
async def handle_docx_upload(event):
    user_id = event.message.peer_id.user_id

    if not await is_expected_steps(user_id, [52]):
        return

    if not event.message.file:
        return
    file_name = event.message.file.name
    if not file_name:
        return

    if file_name.lower().endswith(".docx"):
        await event.client.send_message(
            event.chat_id,
            "Принял файл 👍. Начинаю обработку...",
            buttons=await get_keyboard(["Завершить"])
        )

        try:
            path = await event.message.download_media()
            content = extract_text_from_docx(path)
            os.remove(path)
        except Exception as e:
            keyboard = await get_keyboard(["Завершить"])
            await event.client.send_message(
                event.chat_id,
                "Не удалось прочитать содержимое файла 😔. Проверь его и попробуй еще раз",
                buttons=keyboard
            )
            await update_data_events_db(user_id, "cards_from_file_error", {"step": -1, "error": str(e)})
            return

        if len(content.split()) > 500:
            keyboard = await get_keyboard(["Завершить"])
            await event.client.send_message(
                event.chat_id,
                "Слишком много слов 😔. Попробуй загрузить файл с количеством слов не более 30",
                buttons=keyboard
            )
            await update_data_events_db(user_id, "cards_from_file_error", {"step": -1, "error": "too_many_words"})
            return

        if len(content) < 5:
            keyboard = await get_keyboard(["Завершить"])
            await event.client.send_message(
                event.chat_id,
                "Не удалось прочитать содержимое файла 😔. Проверь его и попробуй еще раз",
                buttons=keyboard
            )
            await update_data_events_db(user_id, "cards_from_file_error", {"step": -1, "error": "zero_content"})
            return

        try:
            card_words = await parse_file(user_id, content)
            card_words = ast.literal_eval(card_words)
            if not isinstance(card_words, dict):
                keyboard = await get_keyboard(["Завершить"])
                await event.client.send_message(
                    event.chat_id,
                    "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜",
                    buttons=keyboard
                )
                await update_data_events_db(user_id, "cards_from_file_error_api", {"step": -1, "error": str(e)})
                return

            await send_error_message(user_id, event, card_words)
            await finalize_cards_and_send_next_steps(event, user_id, card_words, "my_words", next_step=391)

        except Exception as e:
            keyboard = await get_keyboard(["Завершить"])
            await event.client.send_message(
                event.chat_id,
                "Не удалось прочитать содержимое файла 😔. Проверь его и попробуй еще раз",
                buttons=keyboard
            )
            await update_data_events_db(user_id, "cards_from_file_error", {"step": -1, "error": str(e)})
    else:
        keyboard = await get_keyboard(["Завершить"])
        await event.client.send_message(
            event.chat_id,
            "Кажется, это не файл формата .docx 😔\n\nПопробуй еще раз 🕶",
            buttons=keyboard
        )
        await update_data_events_db(user_id, "cards_from_file_error", {"step": -1, "error": "wrong_format"})
