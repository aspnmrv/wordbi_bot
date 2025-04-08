from telethon import events, Button

from db_tools import _get_current_user_step, _update_current_user_step, _get_user_self_words
from db import (
    get_user_level_db,
    get_stat_use_mode_db,
    update_data_events_db,
    update_messages_db
)
from tools import get_keyboard, is_expected_steps
from ellie import get_response
from globals import LIMIT_USES
from config.config import test_user_id
from bot_instance import bot


@bot.on(events.NewMessage(pattern="Quiz me 📝"))
async def get_begin(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    cnt_uses = await get_stat_use_mode_db(user_id)
    if cnt_uses < LIMIT_USES or cnt_uses is None or user_id == test_user_id:
        if await is_expected_steps(user_id, [42]):
            await _update_current_user_step(user_id, 61)

            level = await get_user_level_db(user_id)
            words_list = await _get_user_self_words(user_id)

            async with event.client.action(user_id, "typing"):
                text = await get_response(
                    user_id=user_id,
                    history="",
                    message="",
                    words=words_list,
                    level=level
                )

            buttons = [[Button.inline(text="Перевести", data=49)]]
            await event.client.send_message(event.chat_id, text, buttons=buttons, reply_to=event.message.id)
            await event.client.send_message(
                event.chat_id,
                "Нажми Завершить, если захочешь закончить 🤗",
                buttons=await get_keyboard(["Завершить"])
            )
            await update_messages_db(user_id, "quiz", "ellie", "user", text.replace("'", ""))
            await update_data_events_db(user_id, "quiz_me", {"step": step})
    else:
        await event.client.send_message(event.chat_id, "Слишком много запросов за сегодня 🙂")
        await update_data_events_db(user_id, "quiz_me_error", {"step": -1, "error": "limit"})
