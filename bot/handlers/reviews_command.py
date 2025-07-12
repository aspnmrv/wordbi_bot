from telethon import events

from bot.db_tools import _get_current_user_step, _update_current_user_step
from bot.db import update_data_events_db
from bot.tools import is_expected_steps
from bot.handlers.leave_feedback import leave_feedback_prompt
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="/reviews"))
async def reviews(event):
    user_id = event.message.peer_id.user_id
    if not await is_expected_steps(user_id, [3011, 3010, 2011, 2010, 61, 62]):
        step = await _get_current_user_step(user_id)
        await _update_current_user_step(user_id, 898)
        await update_data_events_db(user_id, "reviews", {"step": step})
        await leave_feedback_prompt(event)
