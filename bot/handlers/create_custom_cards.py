import os

from telethon import events, Button
from bot.tools import get_keyboard, is_expected_steps
from bot.db_tools import _get_current_user_step, _update_current_user_step
from bot.db import update_data_events_db, get_user_categories_db
from bot.bot_instance import bot
from paths import PATH_DEMO


@bot.on(events.NewMessage(pattern="Создать свой набор слов 🧬"))
async def create_self_words(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [41, 545]):
        await _update_current_user_step(user_id, 52)

        categories = await get_user_categories_db(user_id)

        if len(categories) < 10:
            text = (
                "Есть три варианта 🤗 \n\n"
                "1️⃣ Отправь файл (.docx или .txt) со списком слов, которые хочешь выучить.\n\n"
                "Формат в файле:\n"
                "`trip - поездка`\n`house - дом`\n\n"
                "2️⃣ Просто напиши слова здесь.\n\nМожно сразу с переводом:\n"
                "`trip : поездка`\n"
                "`house : дом`\n\n"
                "А можно просто список слов, я сам добавлю перевод:\n`trip`\n`house`\n\n"
                "Каждое слово с новой строки и не менее двух слов 🤏\n\n"
                "3️⃣ Напиши тему или сразу несколько тем, и я сгенерирую карточки. "
                "Учту твой уровень языка 🌱\n\n"
                "Например:\n`IT, Химия, Домашние животные`\n"
            )
            keyboard = await get_keyboard(["Назад"])
            await event.client.send_message(event.chat_id, text, buttons=keyboard, parse_mode="Markdown")
            if os.path.exists(f"{PATH_DEMO}/second_demo.mp4"):
                await event.client.send_file(
                    event.chat_id,
                    file=f"{PATH_DEMO}/second_demo.mp4",
                    caption="А вот краткая инструкция, как можно загрузить слова 🤗",
                    supports_streaming=True
                )
            await update_data_events_db(user_id, "create_words", {"step": step})
        else:
            keyboard = await get_keyboard(["Назад"])
            text = f"У тебя уже сохранено {len(categories)} наборов слов, ого!\n\n" \
                   f"К сожалению, больше {len(categories)} нельзя. Удали " \
                   f"ненужные в разделе /my_cards -> Мои карточки и попробуй снова 🙃"
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "create_words_error", {"step": step, "error": "too_many_categories"})
