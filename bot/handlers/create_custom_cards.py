from telethon import events, Button
from tools import get_keyboard, is_expected_steps
from db_tools import _get_current_user_step, _update_current_user_step
from db import update_data_events_db
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Создать свой набор слов 🧬"))
async def create_self_words(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [41, 545]):
        await _update_current_user_step(user_id, 52)
        text = (
            "Есть три варианта: \n\n1️⃣ Отправь мне тему или сразу несколько тем, "
            "и я сгенерирую карточки по выбранным тобой темам. Твой уровень языка тоже учту 🤗"
            "\nНапример: IT, Химия или Домашние животные\n\n"
            "2️⃣ Отправь слова, которые хочешь выучить: можно сразу с переводом в формате: trip : поездка, "
            "а можно просто список слов, я сам добавлю перевод. Каждое слово с новой строки и не менее "
            "двух слов 🤏\n\n"
            "3️⃣ Отправь файл со списком слов, "
            "которые ты хочешь выучить в форматe <слово на английском> - <перевод слова>. "
            "Файл может быть формата .docx или .doc\n\n⚠️ Но важно, чтобы в файле было не больше 30 слов для изучения, "
            "иначе получится слишком много карточек и будет трудно отслеживать прогресс."
        )
        await event.client.send_message(event.chat_id, text, buttons=Button.clear())
        await update_data_events_db(user_id, "create_words", {"step": step})
