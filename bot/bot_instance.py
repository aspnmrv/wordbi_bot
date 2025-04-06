from telethon import TelegramClient
from config.config import app_id, api_hash, bot_token

bot = TelegramClient("bot", app_id, api_hash).start(bot_token=bot_token)
