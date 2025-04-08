from telethon import events
from db_tools import _get_current_user_step
from db import (
    get_last_message_ellie_db,
    update_data_events_db,
    get_num_translates_db
)

from tools import get_keyboard, is_expected_steps
from ellie import get_translate
from bot_instance import bot


@bot.on(events.CallbackQuery())
async def handle_translate_callback(event):
    user_id = event.original_update.user_id
    step = await _get_current_user_step(user_id)

    if not await is_expected_steps(user_id, [61, 62]):
        return

    data_filter = event.data.decode("utf-8")

    if data_filter == "49":
        last_message = await get_last_message_ellie_db(user_id)
        await update_data_events_db(user_id, "translate_message", {"step": step})

        if last_message:
            last_message = last_message[0]
            translated_text = await get_translate(user_id, last_message)
            num_translates = await get_num_translates_db(user_id)

            if num_translates is None or num_translates == 0:
                translated_text += ">\n\nСтарайся отвечать на английском языке! " \
                                   "Регулярное общение поможет приобрести или " \
                                   "закрепить навык формулирования предложений и сделает более " \
                                   "эффективным запоминание слов 🤓"

            keyboard = await get_keyboard(["Завершить"])
            await event.client.send_message(
                event.chat_id,
                "<" + translated_text + ">",
                buttons=keyboard
            )
            await update_data_events_db(user_id, "translate_message_success", {"step": step})
