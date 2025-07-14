from telethon import events, Button

from bot.db_tools import _get_current_user_step, _update_current_user_step
from bot.db import update_data_events_db
from bot.tools import is_expected_steps, get_code_fill_form, get_users_info
from bot.handlers.leave_feedback import leave_feedback_prompt
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="/my_profile"))
async def my_profile(event):
    user_id = event.message.peer_id.user_id

    if not await is_expected_steps(user_id, [3011, 3010, 2011, 2010, 61, 62]):
        await _update_current_user_step(user_id, 5821)

        code = await get_code_fill_form(user_id)

        if code == -1:
            btn_text_int = "Выбрать интересы"
            btn_text_lev = "Выбрать уровень языка"
        elif code == -3:
            btn_text_int = "Изменить интересы"
            btn_text_lev = "Выбрать уровень языка"
        elif code == -2:
            btn_text_int = "Выбрать интересы"
            btn_text_lev = "Изменить уровень языка"
        else:
            btn_text_int = "Изменить интересы"
            btn_text_lev = "Изменить уровень языка"

        buttons = [
            [Button.inline(btn_text_int, data="profile_int")],
            [Button.inline(btn_text_lev, data="profile_lev")],
        ]

        text = await get_users_info(user_id)
        await event.client.send_message(
            event.chat_id,
            text,
            buttons=buttons
        )
