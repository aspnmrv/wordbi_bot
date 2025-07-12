from telethon import events
from bot.db import update_user_level_db, update_data_events_db
from bot.db_tools import _get_current_user_step, _update_current_user_step
from bot.tools import get_keyboard, is_expected_steps
from bot.bot_instance import bot


async def filter_levels(event):
    user_id = event.message.peer_id.user_id
    if event.message.message in (
        "A1-A2: Beginner 💫",
        "B1-B2: Intermediate ⭐️",
        "C1-C2: Advanced 🌟"
    ):
        await update_user_level_db(user_id, event.message.message)
        return True
    return False


@bot.on(events.NewMessage(func=filter_levels))
async def choose_level(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [2, 41, 42]):
        await _update_current_user_step(user_id, 3)
        keyboard = await get_keyboard(["Карточки слов 🧩", "Чат с Ellie ✨", "Назад"])
        text = (
            "Ты можешь выбрать один из двух режимов:\n\n"
            "1️⃣ Карточки слов 🧩: в этом режиме я сформирую для тебя "
            "список слов для изучения на основе "
            "твоих интересов и текущего уровня языка или ты можешь отправить мне "
            "свои интересы, а я сформирую на их основе список слов.\n\n"
            "2️⃣ Чат с Ellie AI ✨: с ней можно сыграть в игру Quiz me или просто поболтать 🙂"
        )
        await event.client.send_message(event.sender_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "choose_level", {"step": step, "level": event.message.message})
