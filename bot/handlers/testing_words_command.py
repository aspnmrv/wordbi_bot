from telethon import events, Button

from bot.tools import get_keyboard, check_exist_img, create_img_card, is_expected_steps
from bot.db_tools import (
    _get_current_user_step,
    _update_current_user_step,
    _update_user_test_words,
    _get_user_test_words,
    _get_user_self_words
)
from bot.db import update_data_events_db, get_user_words_db
from paths import PATH_IMAGES, PATH_FONT
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Проверить себя 🧠"))
async def testing_words(event):
    async def send_test_word_message(word, step):
        if word is None:
            message = "Ура! Это было последнее слово, хороший результат! " \
                      "😻\n\nЧтобы закончить, нажми на Завершить"
            buttons = await get_keyboard(["Завершить"])
            file = None
            await update_data_events_db(user_id, "testing_complete", {"step": -1})
        else:
            message = ""
            buttons = [[Button.inline(text="Пропустить", data=56)]]
            file = f"{PATH_IMAGES}/{word.replace(' ', '')}_en.png"
            if not await check_exist_img(file):
                await create_img_card(word.replace(' ', '').lower(), file)

        await event.client.send_message(event.chat_id, message, buttons=buttons, file=file)
        if word:
            await _update_user_test_words(user_id, word)
        await _update_current_user_step(user_id, step)

    def get_next_test_word(current, words):
        if current in words:
            i = words.index(current)
            return words[i + 1] if i + 1 < len(words) else None
        return words[0]

    try:
        user_id = event.message.peer_id.user_id
    except AttributeError:
        user_id = event.original_update.user_id

    step = await _get_current_user_step(user_id)
    if await is_expected_steps(user_id, [50, 51, 2011, 3011, 2010, 3010]):
        words = await (get_user_words_db(user_id) if step in [50, 2011, 3011] else _get_user_self_words(user_id))
        if isinstance(words, tuple) and isinstance(words[0], list):
            words = words[0]

        if isinstance(words, list) and isinstance(words[0], list):
            words = words[0]

        current = await _get_user_test_words(user_id)

        if step not in [3011, 3010]:
            intro = "А теперь я буду проверять тебя! 😈 \n\n" \
                    "Я буду тебе показывать карточку на английском языке, а твоя " \
                    "задача написать мне перевод слова на русском языке, " \
                    "которое было написано с обратной стороны " \
                    "карточки 😊\n\n" \
                    "Если не помнишь слово, нажимай на Пропустить\n" \
                    "А если устанешь или надоест, нажимай на пнопку Завершить"
            await event.client.send_message(event.chat_id, intro, buttons=await get_keyboard(["Завершить"]))
            next_word = words[0]
        else:
            next_word = get_next_test_word(current, words)

        next_step = 2011 if step in [50, 2011, 3011] else 2010
        await send_test_word_message(next_word, next_step)
        await update_data_events_db(user_id, "testing", {"step": step})
