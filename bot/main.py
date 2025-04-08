import ast
import os
import sys
import requests
from config import config
import importlib

from pathlib import Path
from telethon.tl.custom import Button
from telethon import TelegramClient, events, sync, functions
from telethon.tl.types import InputPeerChannel
from telethon.tl.types import SendMessageTypingAction
from PIL import Image, ImageDraw, ImageFont, ImageColor

from db_tools import _update_current_user_step, _update_user_states, _get_user_states, \
    _get_current_user_step, _create_db, _update_user_topic_words, \
    _get_user_words, _update_user_words, _update_user_choose_topic, \
    _get_user_self_words, _update_user_self_words, _get_user_test_words, _update_user_test_words
from globals import TOPICS, WORDS, TRANSLATES, LIMIT_TIME_EVENTS, LIMIT_USES, LIMIT_LINK_USES, LIMIT_USES_MESSAGES
from ellie import get_response, build_cards_from_text, get_conversations, get_translate

from tools import update_text_from_state_markup, get_keyboard, find_file, is_expected_steps, \
    build_img_cards, get_proposal_topics, build_markup, get_state_markup, \
    match_topics_name, get_diff_between_ts, build_list_of_words, build_history_message, send_img, check_exist_img, \
    create_img_card, get_translate_word

from db import is_user_exist_db, update_data_users_db, update_data_topics_db, get_user_topics_db, \
    get_user_words_db, update_user_words_db, get_user_level_db, update_user_level_db, \
    update_messages_db, update_reviews_db, update_data_events_db, get_event_from_db, get_stat_use_message_db, \
    get_stat_use_link_db, get_history_chat_ellie_db, get_stat_use_mode_db, \
    get_private_db, get_user_for_notify_reviews_db, get_last_message_ellie_db, get_num_translates_db
from paths import PATH_IMAGES, PATH_FONT
from bot_instance import bot


config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config')
config_path = os.path.abspath(config_path)
sys.path.insert(1, config_path)


api_id = config.app_id
api_hash = config.api_hash
bot_token = config.bot_token
test_user_id = config.test_user_id

# PATH_IMAGES = Path(__file__).resolve().parents[1] / "data" / "images"
HANDLERS_DIR = Path(__file__).parent / "handlers"

# bot = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

print(bot)

history_dict = dict()


def load_handlers(directory: Path):
    for filename in os.listdir(directory):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            import_path = f"{directory.name}.{module_name}"
            importlib.import_module(import_path)


load_handlers(HANDLERS_DIR)

bot.run_until_disconnected()
