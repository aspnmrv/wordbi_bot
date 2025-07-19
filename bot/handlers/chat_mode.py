from telethon import events, Button
from bot.tools import get_keyboard, is_expected_steps
from bot.db_tools import _get_current_user_step, _update_current_user_step
from bot.db import update_data_events_db
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Чат с Ellie ✨"))
async def start_chat(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [1, 6, 9, 545]):
        await _update_current_user_step(user_id, 42)
        keyboard = await get_keyboard(["Поболтать 💌", "Назад"])
        text = (
            "Здесь ты можешь поболтать с Ellie AI на разные темы. Ellie учтет твои "
            "интересы и уровень языка при разговоре 😉\n\nЕсли готов, то нажимай на Поболтать 💌"
        )
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "chat", {"step": step})
