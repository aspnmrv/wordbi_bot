from telethon import events

from db_tools import _get_current_user_step, _update_current_user_step
from db import update_data_events_db, get_user_stat_new_words_db, get_user_stat_learned_words_db, get_user_stat_total_db
from tools import get_keyboard, is_expected_steps, draw_words_line_chart, send_user_file_stat, draw_words_category_chart
from bot_instance import bot


@bot.on(events.NewMessage(pattern="/my_stat"))
async def get_my_stat(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    # if await is_expected_steps(user_id, [7]):
    # await _update_current_user_step(user_id, 888)
    await update_data_events_db(user_id, "get_stat", {"step": -1})

    cnt_new_words = await get_user_stat_new_words_db(user_id)
    cnt_learned_words = await get_user_stat_learned_words_db(user_id)
    total_words_stat = await get_user_stat_total_db(user_id)

    categories = [row[0].lower() for row in total_words_stat if row[0]]
    words = [row[1] for row in total_words_stat if row[0]]
    learned_words = [row[2] for row in total_words_stat if row[0]]
    shares = [row[3] for row in total_words_stat if row[0]]

    # keyboard = await get_keyboard(["Карточки слов 🧩", "Чат с Ellie 💬"])
    if cnt_new_words:
        dates = [d[0] for d in cnt_new_words]
        viewed_cards = [d[1] for d in cnt_new_words]
        learned_cards = [d[1] for d in cnt_learned_words]

        text = f"Что по прогрессу? 💜\n\n\n" \
               f"У тебя {sum(viewed_cards)} просмотренных карточки\n\n" \
               f"🦾 {sum(learned_cards)} успешно изученных слов\n\n" \
               f"📊 Любимая категория: {categories[0]}\n\n"
        await event.client.send_message(
            event.chat_id,
            text,
            # buttons=keyboard
        )

        if len(dates) > 1:
            file_viewed_cards = await draw_words_line_chart(cnt_new_words)
            await send_user_file_stat(event, file_viewed_cards, "✨Количество просмотренных карточек по дням")

            file_learned_cards = await draw_words_line_chart(cnt_learned_words)
            await send_user_file_stat(event, file_learned_cards, "⭐️ Количество выученных карточек по дням")
        else:
            await event.client.send_message(
                event.chat_id,
                "А спустя несколько дней изучения слов, когда накопятся данные, "
                "у тебя здесь появится график с динамикой твоего прогресса 😏\n\n",
                # buttons=keyboard
            )

        if len(categories) > 1:
            file = await draw_words_category_chart(total_words_stat)
            await send_user_file_stat(event, file, "Прогресс по изученным категориям 📈")
        else:
            await event.client.send_message(
                event.chat_id,
                f"У тебя {words[0]} просмотренных карточки в категории {categories[0]}\n"
                f"Из них {learned_words[0]} ({shares[0]}% слов ты уже выучил 🧠",
                # buttons=keyboard
            )
    else:
        await event.client.send_message(
            event.chat_id,
            "Пока нет данных с личной статистикой. Но никогда не поздно начать по команде /start 😏",
            # buttons=keyboard
        )
