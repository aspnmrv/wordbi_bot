from telethon import events
from db_tools import _get_current_user_step, _update_current_user_step
from db import update_data_events_db
from tools import get_keyboard, is_expected_steps
from bot_instance import bot


@bot.on(events.NewMessage(pattern="Выбрать другой режим ⚙️"))
async def choose_other_mode(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [7]):
        await _update_current_user_step(user_id, 9)
        keyboard = await get_keyboard(["Карточки слов 🧩", "Чат с Ellie 💬"])
        await event.client.send_message(event.chat_id, "Попробуем что-то другое? 😏", buttons=keyboard)
        await update_data_events_db(user_id, "other_mode", {"step": step})
