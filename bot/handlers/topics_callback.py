from telethon import events
from bot.tools import build_markup, update_text_from_state_markup, get_state_markup
from bot.db_tools import _get_user_states
from bot.tools import match_topics_name
from bot.db_tools import _get_current_user_step
from bot.bot_instance import bot


@bot.on(events.CallbackQuery())
async def handle_topics_callback(event):

    user_id = event.original_update.user_id
    step = await _get_current_user_step(user_id)

    if step not in [1, 2]:
        return

    async def gather_user_states(user_id):
        current_topics = await _get_user_states(user_id, "topics")
        current_state = await _get_user_states(user_id, "states")
        current_topics = await match_topics_name(current_topics)
        return current_topics, current_state

    topic_clicked = event.data.split(b"$")[0].decode("utf-8")
    current_topics, current_state = await gather_user_states(user_id)

    markup = bot.build_reply_markup(await build_markup(current_topics, current_state))
    await update_text_from_state_markup(markup, current_state, current_topics, topic_clicked)
    await get_state_markup(markup, user_id)
    await event.client.edit_message(event.sender_id, event.message_id, buttons=markup)
