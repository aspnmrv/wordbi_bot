from telethon import events
from tools import get_keyboard, is_expected_steps
from db_tools import _get_current_user_step, _update_current_user_step
from db import update_data_events_db
from bot_instance import bot


@bot.on(events.NewMessage(pattern="Карточки слов 🧩"))
async def cards(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [3, 51, 52, 9]):
        await _update_current_user_step(user_id, 41)
        keyboard = await get_keyboard([
            "Карточки на основе интересов 👾",
            "Создать свой набор слов 🧬",
            "Назад"
        ])
        text = (
            "Создать набор карточек на основе твоих интересов или хочешь создать свой набор слов?\n\n"
            "👾 Карточки на основе интересов - я создам карточки на основе интересов, которые ты уже выбрал\n"
            "🧬 Создать свой набор слов - в этом режиме я автоматически сгенерирую карточки на основе тем, "
            "которые ты мне пришлешь 🤓"
        )
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "cards", {"step": step})
