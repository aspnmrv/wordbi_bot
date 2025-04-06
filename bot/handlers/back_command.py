from telethon import events
from db_tools import _get_current_user_step
from tools import is_expected_steps
from handlers.start import start
from handlers.begin import begin
from handlers.confirm_topics import confirmed
from handlers.choose_level import choose_level
from handlers.cards_entry import cards
from handlers.chat_mode import start_chat
from handlers.finish_command import get_end
from bot_instance import bot


@bot.on(events.NewMessage(pattern="Назад"))
async def get_back(event):
    user_id = event.message.peer_id.user_id

    if await is_expected_steps(user_id, [1]):
        await start(event)
    elif await is_expected_steps(user_id, [2]):
        await begin(event)
    elif await is_expected_steps(user_id, [3]):
        await confirmed(event)
    elif await is_expected_steps(user_id, [41, 42]):
        await choose_level(event)
    elif await is_expected_steps(user_id, [52]):
        await cards(event)
    elif await is_expected_steps(user_id, [6]):
        await start_chat(event)
    elif await is_expected_steps(user_id, [11]):
        await start(event)
    elif await is_expected_steps(user_id, [10, 676, 62]):
        await get_end(event)
