from telethon import events, Button
from bot.db_tools import _get_current_user_step, _update_current_user_step, _get_user_self_words
from bot.db import update_data_events_db
from bot.tools import is_expected_steps, get_code_fill_form
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="/my_cards"))
async def get_my_cards(event):
    user_id = event.message.peer_id.user_id
    code = await get_code_fill_form(user_id)

    if code == -4:
        await event.client.send_message(
            event.chat_id,
            "Еще нет карточек ☺️\n\nНажимай на /start, чтобы добавить их",
            buttons=Button.clear()
        )
        await update_data_events_db(user_id, "my_cards", {"step": -1, "error": "without cards"})
    else:
        if not await is_expected_steps(user_id, [3011, 3010, 2011, 2010, 61, 62]):
            step = await _get_current_user_step(user_id)
            await _update_current_user_step(user_id, 545)

            text = "Выбери тип карточек, которые нужно открыть🤗\n\n"
            text += "▪️ База – карточки, созданные на основе твоих интересов и уровня языка\n"
            text += "▪️ Мои карточки – карточки, созданные из своего набора слов или из файла"

            buttons = [[
                Button.inline("База", data=10),
                Button.inline("Мои карточки", data=11),
            ]]

            await event.client.send_message(event.chat_id, text, buttons=buttons)
            await update_data_events_db(user_id, "my_cards", {"step": step})
