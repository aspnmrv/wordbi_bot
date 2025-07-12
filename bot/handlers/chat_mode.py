from telethon import events, Button
from tools import get_keyboard, is_expected_steps
from db_tools import _get_current_user_step, _update_current_user_step
from db import update_data_events_db
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Чат с Ellie ✨"))
async def start_chat(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [3, 6, 9]):
        await _update_current_user_step(user_id, 42)
        keyboard = await get_keyboard(["Quiz me 📝", "Поболтать 💌", "Назад"])
        text = (
            "Выбери один из двух режимов:\n\n"
            "Quiz me 📝 - в этом режиме Ellie AI будет спрашивать у тебя значения слов, "
            "которые я тебе подобрал на основе твоих интересов, "
            "а твоя задача объяснить их значение. На английском языке, конечно же 😏\n\n"
            "А если просто хочешь поболтать с Ellie AI, то выбирай режим Поболтать 💌\n"
            "Ellie учтет твои интересы и уровень языка 😉"
        )
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "chat", {"step": step})
