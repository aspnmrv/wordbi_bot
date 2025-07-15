from telethon import events, Button
from bot.tools import get_keyboard, is_expected_steps
from bot.db_tools import _get_current_user_step, _update_current_user_step
from bot.db import update_data_events_db, get_user_categories_db
from bot.bot_instance import bot
from bot.decorators import limit_usage


@bot.on(events.NewMessage(pattern="Создать свой набор слов 🧬"))
@limit_usage("start_conversation_mode", 50)
async def create_self_words(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [41, 545]):
        await _update_current_user_step(user_id, 52)

        categories = await get_user_categories_db(user_id)

        if len(categories) < 10:
            text = (
                "Есть три варианта: \n\n"
                "1️⃣ Отправь файл со списком слов, "
                "которые ты хочешь выучить в форматe <слово на английском> - <перевод слова>. "
                "Файл может быть формата .docx или .txt\n\n"
                "2️⃣ Отправь слова, которые хочешь выучить: можно сразу с переводом в формате: trip : поездка, "
                "а можно просто список слов, я сам добавлю перевод. Каждое слово с новой строки и не менее "
                "двух слов 🤏\n\n"
                "3️⃣ Отправь мне тему или сразу несколько тем, "
                "и я сгенерирую карточки по выбранным тобой темам. Твой уровень языка тоже учту 🤗"
                "\nНапример: IT, Химия или Домашние животные\n\n"
            )
            keyboard = await get_keyboard(["Назад"])
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "create_words", {"step": step})
        else:
            keyboard = await get_keyboard(["Назад"])
            text = f"У тебя уже сохранено {len(categories)} наборов слов, ого!\n\n" \
                   f"К сожалению, больше {len(categories)} нельзя. Удали " \
                   f"ненужные в разделе /my_cards -> Мои карточки и попробуй снова 🙃"
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "create_words_error", {"step": step, "error": "too_many_categories"})
