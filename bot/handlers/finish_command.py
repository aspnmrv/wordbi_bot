from telethon import events, Button
from bot.db_tools import _get_current_user_step, _update_current_user_step, _get_user_main_mode
from bot.db import update_data_events_db
from bot.tools import get_keyboard, is_expected_steps
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Завершить"))
async def get_end(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)
    main_mode = await _get_user_main_mode(user_id)

    if await is_expected_steps(user_id, [52, 101, 61, 62, 51, 41, 2011, 3011, 2010, 3010,
                                         901, 10, 50, 676, 4010, 4011, 5010, 7, 904, 902]):
        await _update_current_user_step(user_id, 7)
        keyboard = await get_keyboard(["Выбрать другой режим ⚙️", "Оставить отзыв 💌"])

        text = "Хорошо! Чтобы вернуться к просмотру карточек слов, выбери в боковом меню команду /my_cards 🙃\n\n" \
               "А чтобы увидеть статистику по своему прогрессу, можешь запустить команду /my_stat в боковом меню"
        await event.client.send_message(event.chat_id, text, buttons=keyboard)

        if main_mode and not await is_expected_steps(user_id, [52]):
            opposite_mode = "ru_en" if main_mode == "en_ru" else "en_ru"
            if opposite_mode == "ru_en":
                opposite_text = "📝 Хочешь попробовать теперь перевести с русского на английский?"
                opposite_data = "test_ru_en"
            else:
                opposite_text = "📚 Хочешь попробовать теперь перевести с английского на русский?"
                opposite_data = "test_en_ru"

            keyboard += [[Button.inline(opposite_text, data=opposite_data)]]

            await event.client.send_message(
                event.chat_id,
                opposite_text,
                buttons=[[Button.inline("Да, давай попробуем!", data=opposite_data)]]
            )

        await update_data_events_db(user_id, "complete", {"step": step})
