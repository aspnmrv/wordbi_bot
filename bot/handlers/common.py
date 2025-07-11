from tools import get_keyboard, build_img_cards
from db_tools import (
    _update_user_self_words, _update_current_user_step,
    _update_user_words, _update_user_choose_topic
)
from db import update_user_words_db, update_data_events_db, update_user_stat_category_words_db


async def finalize_cards_and_send_next_steps(event, user_id, card_words, topic, next_step):
    await _update_user_self_words(user_id, card_words)
    fixed = {w.replace('/', ''): t.replace('/', '') for w, t in card_words.items()}
    await build_img_cards(fixed)
    await _update_user_words(user_id, "self", "", "en")
    await _update_user_choose_topic(user_id, "self")
    await update_user_words_db(user_id, fixed, topic)
    await event.client.send_message(
        event.chat_id,
        "Чтобы увидеть карточки, жмякай на Увидеть карточки 💜",
        buttons=await get_keyboard(["Увидеть карточки 💜"])
    )
    await update_data_events_db(user_id, "cards_success", {"step": next_step})
    await _update_current_user_step(user_id, next_step)
    await update_user_stat_category_words_db(user_id, list(fixed.keys()), topic)
