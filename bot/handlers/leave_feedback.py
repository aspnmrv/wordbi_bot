from telethon import events
from tools import get_keyboard, is_expected_steps
from db_tools import _get_current_user_step, _update_current_user_step
from db import update_data_events_db
from bot_instance import bot


@bot.on(events.NewMessage(pattern="Оставить отзыв 💌"))
async def leave_feedback_prompt(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [7, 8, 898]):
        await _update_current_user_step(user_id, 10)
        keyboard = await get_keyboard(["Назад"])
        text = "Буду очень рад, если поделишься своим впечатлением! Для этого просто отправь мне сообщение 💜"
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "leave_feedback", {"step": step})
