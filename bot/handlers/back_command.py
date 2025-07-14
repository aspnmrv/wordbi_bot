from telethon import events

from bot.tools import is_expected_steps
from bot.handlers.start import start
from bot.handlers.begin import begin
from bot.handlers.confirm_topics import confirmed
from bot.handlers.choose_level import choose_level
from bot.handlers.cards_entry import cards
from bot.handlers.chat_mode import start_chat
from bot.handlers.finish_command import get_end
from bot.handlers.my_profile import my_profile
from bot.db_tools import _get_current_user_step
from bot.handlers.callback_get_cards import show_categories_menu
from bot.handlers.my_cards_command import get_my_cards
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Назад"))
async def get_back(event):
    user_id = event.message.peer_id.user_id

    if await is_expected_steps(user_id, [1]):
        await start(event)
    elif await is_expected_steps(user_id, [2]):
        await my_profile(event)
    elif await is_expected_steps(user_id, [3]):
        await my_profile(event)
    elif await is_expected_steps(user_id, [5821]):
        await begin(event)
    elif await is_expected_steps(user_id, [41, 42]):
        await begin(event)
    elif await is_expected_steps(user_id, [52]):
        await cards(event)
    elif await is_expected_steps(user_id, [6]):
        await start_chat(event)
    elif await is_expected_steps(user_id, [11]):
        await start(event)
    elif await is_expected_steps(user_id, [10, 676, 62]):
        await get_end(event)
    elif await is_expected_steps(user_id, [51]):
        await cards(event)
    elif await is_expected_steps(user_id, [903]):
        await show_categories_menu(event, user_id, is_system_words=False)
    elif await is_expected_steps(user_id, [907]):
        await show_categories_menu(event, user_id, is_system_words=True)
    elif await is_expected_steps(user_id, [902]):
        await get_my_cards(event)
    elif await is_expected_steps(user_id, [52]):
        await cards(event)
    elif await is_expected_steps(user_id, [904]):
        await get_my_cards(event)
    elif await is_expected_steps(user_id, [545]):
        await cards(event)
