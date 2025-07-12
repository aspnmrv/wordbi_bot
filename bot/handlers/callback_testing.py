from telethon import events

from bot.db_tools import _get_current_user_step, _update_current_user_step
from bot.tools import is_expected_steps
from bot.handlers.testing_words_command import testing_words
from bot.db import update_data_events_db
from bot.bot_instance import bot


@bot.on(events.CallbackQuery())
async def handle_testing_callback(event):
    user_id = event.original_update.user_id
    step = await _get_current_user_step(user_id)

    if not await is_expected_steps(user_id, [2010, 2011]):
        return

    data_filter = event.data.decode("utf-8")

    if data_filter == "56":
        if await is_expected_steps(user_id, [2010]):
            await _update_current_user_step(user_id, 3010)
            await testing_words(event)
        elif await is_expected_steps(user_id, [2011]):
            await _update_current_user_step(user_id, 3011)
            await testing_words(event)

        await update_data_events_db(user_id, "testing_start", {"step": step})
