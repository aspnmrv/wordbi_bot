from telethon import events, Button

from bot.tools import get_keyboard, send_img, build_list_of_words, \
    is_expected_steps, get_code_fill_form, match_topics_name, get_image_filename, normalize_filename
from bot.db_tools import (
    _get_current_user_step,
    _update_current_user_step,
    _update_user_words,
    _update_user_self_words,
    _get_user_choose_category
)
from bot.db import (
    get_user_topics_db,
    get_user_level_db,
    get_user_words_db,
    update_data_events_db,
    update_user_stat_words_db,
    get_user_words_by_category_db
)
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="👾 База"))
async def get_start_cards(event):
    try:
        user_id = event.message.peer_id.user_id
    except:
        user_id = event.original_update.user_id

    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [41, 101, 501, 901, 545]):
        topics = await get_user_topics_db(user_id)
        user_level = await get_user_level_db(user_id)

        if await is_expected_steps(user_id, [901]):
            await event.client.send_message(event.chat_id, "Подбираю слова..", buttons=Button.clear())
            category = await _get_user_choose_category(user_id=user_id)
            category = category[0]
            words_list = await get_user_words_by_category_db(user_id=user_id, category=category)
            words_list = list(words_list.keys())
            await _update_current_user_step(user_id, 50)
            current_word = words_list[0].lower()
            topic = category

            buttons = [[
                Button.inline(text="⬅️", data=-1),
                Button.inline("🔄", data=0),
                Button.inline("➡️", data=1),
            ]]

            keyboard = await get_keyboard(["Проверить себя 🧠", "Завершить"])
            text = (
                "Сформировал для тебя набор слов, начнем? ☄️\n\n"
                "Как пользоваться карточками?\n\n"
                "➡️ - листать вперед\n🔄 - перевернуть карточку (показать перевод)\n⬅️ - листать назад\n\n"
                "Проверить себя🧠 - нажимай, если захочешь проверить свои знания!\n\n"
                "А если устанешь или надоест, можно закончить, нажав на кнопку Завершить"
            )

            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await send_img(
                event=event,
                buttons=buttons,
                file_name=get_image_filename(user_id, normalize_filename(current_word), "en", normalize_filename(category)),
                current_word=current_word,
                lang="en",
                type_action="send"
            )
            await _update_user_words(user_id, topic, current_word, "en")
            await update_data_events_db(user_id, "cards_interests", {"step": step})
            await update_user_stat_words_db(user_id, current_word)
        else:
            await _update_current_user_step(user_id, 51)
            code = await get_code_fill_form(user_id)
            if code in (-1, -3):
                text = "Чтобы увидеть базовые слова, которые я подготовил, необходимо выбрать " \
                       "интересы и уровень языка 🙂\n\nЭто поможет мне сделать для тебя самые полезные подборки слов." \
                       "\n\nДля добавления интересов и уровня воспользуйся командой /my_profile"
                keyboard = await get_keyboard(["Назад"])
                await event.client.send_message(event.chat_id, text, buttons=keyboard)
                return
            else:
                await event.client.send_message(event.chat_id, "Собираю подборки..", buttons=Button.clear())

                words = await build_list_of_words(topics, user_level, user_id)
                categories = set([cat for cat in words.values()])
                buttons = []
                for cat in categories:
                    buttons.append([Button.inline(text=cat, data=f"base_cat:{cat}")])

                text = "Собрал для тебя подборки, учитывая выбранные интересы и уровень языка 😊\n\n" \
                       "Можешь выбрать любую и увидеть список слов, а затем потренироваться!"
                await event.client.send_message(event.chat_id, text, buttons=buttons)

                await _update_current_user_step(user_id, 51)
