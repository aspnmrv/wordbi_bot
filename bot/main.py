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

from bot_instance import bot


config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config')
config_path = os.path.abspath(config_path)
sys.path.insert(1, config_path)


api_id = config.app_id
api_hash = config.api_hash
bot_token = config.bot_token
test_user_id = config.test_user_id

HANDLERS_DIR = Path(__file__).parent / "handlers"

history_dict = dict()


def load_handlers(directory: Path):
    for filename in os.listdir(directory):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            import_path = f"{directory.name}.{module_name}"
            importlib.import_module(import_path)


load_handlers(HANDLERS_DIR)

bot.run_until_disconnected()
