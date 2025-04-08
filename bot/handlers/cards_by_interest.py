from telethon import events, Button

from tools import get_keyboard, send_img, build_list_of_words, is_expected_steps
from db_tools import (
    _get_current_user_step,
    _update_current_user_step,
    _update_user_words,
    _update_user_self_words
)
from db import (
    get_user_topics_db,
    get_user_level_db,
    get_user_words_db,
    update_data_events_db
)
from bot_instance import bot


@bot.on(events.NewMessage(pattern="Карточки на основе интересов 👾"))
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
            words_list = await get_user_words_db(user_id)
            words_list = words_list[0]
            await _update_current_user_step(user_id, 50)
            current_word = words_list[0].lower()
        else:
            words_list = await build_list_of_words(topics, user_level)
            await _update_user_self_words(user_id, words_list)
            current_word = words_list[0].lower()
            await _update_current_user_step(user_id, 51)

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
            file_name=f"{current_word.replace(' ', '')}_en.png",
            current_word=current_word,
            lang="en",
            type_action="send"
        )

        await _update_user_words(user_id, "sport", current_word, "en")
        await update_data_events_db(user_id, "cards_interests", {"step": step})
