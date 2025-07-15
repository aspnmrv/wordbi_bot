from telethon import events
from bot.tools import get_keyboard, is_expected_steps
from bot.db_tools import _get_current_user_step, _update_current_user_step
from bot.db import update_data_events_db
from bot.bot_instance import bot
from bot.decorators import limit_usage


@bot.on(events.NewMessage(pattern="Обо мне 👾"))
async def about_me(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [0]):
        await _update_current_user_step(user_id, 11)
        keyboard = await get_keyboard(["Назад"])
        text = (
            "Хэй!\n\nЯ бот, созданный с целью помочь расширить словарный запас.\n\n"
            "Вместе со мной ты можешь создать карточки слов и пообщаться с Ellie AI, "
            "которая работает на базе моделей от Open AI 👾"
        )
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "about_me", {"step": step})
