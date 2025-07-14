from telethon import events, Button

from bot.tools import get_keyboard, build_img_cards
from bot.db_tools import (
    _update_user_self_words, _update_current_user_step,
    _update_user_words, _update_user_choose_topic
)
from bot.db import update_user_words_db, update_data_events_db, update_user_stat_category_words_db


async def finalize_cards_and_send_next_steps(event, user_id, card_words, topic, next_step, is_cut: bool = False):
    """"""
    await _update_user_self_words(user_id, card_words)
    fixed = {w.replace('/', ''): t.replace('/', '') for w, t in card_words.items()}
    await build_img_cards(fixed, user_id)
    await _update_user_words(user_id, "self", "", "en")
    await _update_user_choose_topic(user_id, "self")
    await update_user_words_db(user_id, fixed, topic)
    if not is_cut:
        await event.client.send_message(
            event.chat_id,
            "Почти все готово..\n\nВведи название для этой подборки, чтобы ты всегда мог вернуться к ней",
            buttons=Button.clear()
        )
    else:
        await event.client.send_message(
            event.chat_id,
            "Список слов был слишком длинный. Пришлось его немного обрезать\n\n"
            "Почти все готово..\n\nВведи название для этой подборки, чтобы ты всегда мог вернуться к ней",
            buttons=Button.clear()
        )
    await update_data_events_db(user_id, "cards_success", {"step": next_step})
    await _update_current_user_step(user_id, next_step)
    await update_user_stat_category_words_db(user_id, fixed, topic, is_system=False)


async def check_wrong_message(result):
    """"""

    if not result:
        return False
    if not isinstance(result, dict):
        return False

    if list(result.keys())[0] in (-1, -2, -3):
        return True
    else:
        return False


async def send_error_message(user_id, event, result):
    """"""
    if not result:
        return
    if not isinstance(result, dict):
        return

    is_wrong = await check_wrong_message(result)

    if is_wrong:
        type_error = list(result.keys())[0]
        if type_error == -1:
            error_message = "content"
            user_message = "Среди этих слов есть весьма специфичные 😔. Попробуй еще раз.."
        elif type_error == -2:
            error_message = "too_much_words"
            user_message = "Слишком много слов 😔. Попробуй c количеством слов не более 30."
        elif type_error == -3:
            error_message = "other language"
            user_message = "Кажется, с такими языками я еще не умею работать 😔. Используй EN, RU слова."
        else:
            error_message = f"type_error_{type_error}"
            user_message = "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜"

        keyboard = await get_keyboard(["Завершить"])
        await event.client.send_message(
            event.chat_id,
            user_message,
            buttons=keyboard
        )
        await update_data_events_db(user_id, "own_cards", {"step": -1, "error": error_message})
    else:
        return
