from telethon import events

from db_tools import _update_current_user_step
from tools import is_expected_steps
from handlers.cards_by_interest import get_start_cards
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Увидеть карточки 💜"))
async def see_cards(event):
    user_id = event.message.peer_id.user_id
    if await is_expected_steps(user_id, [101, 391]):
        await _update_current_user_step(user_id, 901)
        await get_start_cards(event)
