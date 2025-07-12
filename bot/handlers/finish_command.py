from telethon import events
from bot.db_tools import _get_current_user_step, _update_current_user_step
from bot.db import update_data_events_db
from bot.tools import get_keyboard, is_expected_steps
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Завершить"))
async def get_end(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [52, 101, 61, 62, 51, 41, 2011, 3011, 2010, 3010, 901, 10, 50, 676]):
        await _update_current_user_step(user_id, 7)
        keyboard = await get_keyboard(["Выбрать другой режим ⚙️", "Оставить отзыв 💌"])
        text = "Хорошо! Чтобы вернуться к просмотру карточек слов, выбери в боковом меню команду /my_cards 🙃\n\n" \
               "А чтобы увидеть статистику по своему прогрессу, можешь запустить команду /my_stat в боковом меню"
        text += "А здесь ты можешь выбрать другой режим или оставить отзыв 💜"
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "complete", {"step": step})
