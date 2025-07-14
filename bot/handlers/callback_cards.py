from telethon import events
from telethon.tl.custom import Button
from bot.tools import get_keyboard, send_img, get_translate_word, match_topics_name, is_expected_steps
from bot.db_tools import (
    _get_current_user_step, _get_user_words, _get_user_self_words, _update_user_words,
    _get_user_states, _update_current_user_step, _get_user_choose_category
)
from bot.db import (
    get_user_words_db,
    update_data_events_db,
    get_last_message_ellie_db,
    get_num_translates_db,
    update_user_stat_words_db,
    get_user_words_by_category_db
)
from bot.bot_instance import bot


@bot.on(events.CallbackQuery())
async def handle_card_callback(event):
    user_id = event.original_update.user_id
    step = await _get_current_user_step(user_id)

    async def process_refresh():
        state = await _get_user_words(user_id)
        current_topic, current_word, current_lang = state[0]

        buttons = [[
            Button.inline(text="⬅️", data=-1),
            Button.inline(text="🔄", data=0),
            Button.inline(text="➡️", data=1),
        ]]

        user_self_words = await _get_user_self_words(user_id)
        lang = "ru" if current_lang == "en" else "en"

        if lang == "ru":
            try:
                current_word_new = await get_translate_word(word=current_word, from_lang="en")
            except:
                current_word_new = next((v for k, v in user_self_words.items()
                                         if k.lower() == current_word.lower()), None)
        else:
            current_word_new = current_word

        await send_img(event, buttons, f"{current_word.replace(' ', '')}_{lang}.png", current_word_new, lang, "edit")
        await _update_user_words(user_id, "sport", current_word, lang)
        await update_data_events_db(user_id, "refresh_card", {"step": step})

    async def process_forward():
        if await is_expected_steps(user_id, [50]):
            category = await _get_user_choose_category(user_id)
            category = category[0]
            words_list = await get_user_words_by_category_db(user_id, category)
            words_list = list(words_list.keys())
            state = await _get_user_words(user_id)
            current_word = state[0][1].lower()
            new_current_word = current_word
        else:
            state = await _get_user_words(user_id)
            current_word = state[0][1]

            category = await _get_user_choose_category(user_id)
            category = category[0]
            words_list = await get_user_words_by_category_db(user_id, category)
            words_list = list(words_list.keys())
            new_current_word = current_word

        for i in range(len(words_list) - 1):
            if words_list[i].lower() == current_word.lower():
                new_current_word = words_list[i + 1].lower()

        if new_current_word == current_word:
            buttons = [
                [
                    Button.inline(text="⬅️", data=-1),
                    Button.inline(text="🔄", data=0),
                ],
            ]
            await send_img(
                event=event,
                buttons=buttons,
                file_name=f"{current_word.replace(' ', '')}_en.png",
                current_word=current_word,
                lang="en",
                type_action="edit"
            )

            keyboard = await get_keyboard(["Проверить себя 🧠", "Завершить"])
            text = "Карточки закончились, но ты можешь продолжать их листать и переворачивать, " \
                   "а также можешь проверить свои знания по кнопке Проверить себя 🧠\n"
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "complete_card", {"step": -1})
            await update_user_stat_words_db(user_id, current_word)
        else:
            current_word = new_current_word
            buttons = [
                [
                    Button.inline(text="⬅️", data=-1),
                    Button.inline(text="🔄", data=0),
                    Button.inline(text="➡️", data=1),
                ],
            ]
            await send_img(
                event=event,
                buttons=buttons,
                file_name=f"{current_word.replace(' ', '')}_en.png",
                current_word=current_word,
                lang="en",
                type_action="edit"
            )

            await _update_user_words(user_id, category, current_word, "en")
            await update_data_events_db(user_id, "forward_card", {"step": step})
            await update_user_stat_words_db(user_id, current_word)

    async def process_backward():
        if await is_expected_steps(user_id, [50]):
            category = await _get_user_choose_category(user_id)
            category = category[0]
            words_list = await get_user_words_by_category_db(user_id, category)
            words_list = list(words_list.keys())
            state = await _get_user_words(user_id)
            current_word = state[0][1]
            current_word = current_word.lower()
            new_current_word = current_word
        else:
            state = await _get_user_words(user_id)
            current_word = state[0][1]
            category = await _get_user_choose_category(user_id)
            category = category[0]
            words_list = await get_user_words_by_category_db(user_id, category)
            words_list = list(words_list.keys())
            new_current_word = current_word

        for i in range(1, len(words_list)):
            if words_list[i].lower() == current_word.lower():
                new_current_word = words_list[i - 1].lower()
        if new_current_word == current_word:
            buttons = [
                [
                    Button.inline(text="🔄", data=0),
                    Button.inline(text="➡️", data=1),
                ],
            ]
            await send_img(
                event=event,
                buttons=buttons,
                file_name=f"{current_word.replace(' ', '')}_en.png",
                current_word=current_word,
                lang="en",
                type_action="edit"
            )

            await update_data_events_db(user_id, "backward_card_first", {"step": step})
        else:
            current_word = new_current_word

            buttons = [
                [
                    Button.inline(text="⬅️", data=-1),
                    Button.inline(text="🔄", data=0),
                    Button.inline(text="➡️", data=1),
                ],
            ]
            await send_img(
                event=event,
                buttons=buttons,
                file_name=f"{current_word.replace(' ', '')}_en.png",
                current_word=current_word,
                lang="en",
                type_action="edit"
            )

            await _update_user_words(user_id, category, current_word, "en")
            await update_data_events_db(user_id, "backward_card", {"step": step})
        return

    if await is_expected_steps(user_id, [50, 501, 51]):
        data_filter = event.data.decode("utf-8")
        if data_filter in ["⬅️", "-1"]:
            await process_backward()
        elif data_filter in ["➡️", "1"]:
            await process_forward()
        elif data_filter == "🔄":
            await process_refresh()
