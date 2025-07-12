from telethon import events, Button
from db import update_reviews_db, update_data_events_db
from tools import is_expected_steps
from bot.bot_instance import bot


@bot.on(events.NewMessage())
async def handle_review_message(event):
    user_id = event.message.peer_id.user_id
    message_text = event.message.message

    if event.message.out:
        return

    if event.message.message == "Оставить отзыв 💌":
        return

    if not await is_expected_steps(user_id, [10]):
        return

    if message_text in ("Назад", "/reviews", "/interests", "/level", "/my_cards", "/start"):
        return

    await update_reviews_db(user_id, message_text)
    await update_data_events_db(user_id, "success_review", {"step": -1})
    await event.client.send_message(event.chat_id, "Спасибо! 💜\n\nКстати, можешь"
                                                   "смотреть статистику своего прогресса по команде /my_stat"
                                                   " из бокового меню 💫")
