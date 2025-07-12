from telethon import events, Button

from db_tools import _get_current_user_step, _update_current_user_step, _get_user_self_words
from db import get_user_words_db
from tools import get_keyboard
from handlers.cards_by_interest import get_start_cards
from db import update_data_events_db
from tools import is_expected_steps
from bot.bot_instance import bot


@bot.on(events.CallbackQuery())
async def handle_get_cards_callback(event):
    user_id = event.original_update.user_id
    step = await _get_current_user_step(user_id)

    if not await is_expected_steps(user_id, [545]):
        return

    data_filter = event.data.decode("utf-8")

    if data_filter == "10":
        await get_start_cards(event)
    else:
        user_words = await get_user_words_db(user_id)

        if user_words:
            await _update_current_user_step(user_id, 901)
            await get_start_cards(event)
        else:
            text = "Кажется, еще не добавлены свои наборы слов. Добавим? 🐱"
            keyboard = await get_keyboard(["Создать свой набор слов 🧬", "Завершить"])
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "my_cards", {"step": -1, "error": "without cards"})

    await update_data_events_db(user_id, "get_cards", {"step": step})
