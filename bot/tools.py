import config
import asyncio
import os, fnmatch
import requests
import random
import itertools

from pathlib import Path
from datetime import datetime
from telethon.tl.custom import Button
from telethon import TelegramClient, events, sync, functions
from telethon.tl.types import InputPeerChannel
from telethon.tl.types import SendMessageTypingAction
from PIL import Image, ImageDraw, ImageFont, ImageColor
from telethon.events import NewMessage
from telethon.tl.custom import Button
from typing import List, Literal, Tuple, Dict, Optional, Any

from db_tools import _update_user_states, _get_current_user_step, _get_user_words
from db import get_user_topics_db, get_user_level_db
from globals import TOPICS, WORDS, TRANSLATES
from paths import PATH_IMAGES, PATH_FONT


async def update_text_from_state_markup(
    markup: Any,
    state: List[str],
    topics: List[str],
    name: str
) -> Any:
    """Forming text for buttons depending on their state"""
    for elem in range(len(state)):
        if topics[elem] == name:
            if "✅" not in markup.rows[elem].buttons[0].text:
                markup.rows[elem].buttons[0].text += " ✅"
            else:
                markup.rows[elem].buttons[0].text = markup.rows[elem].buttons[0].text.split("✅")[0]
        else:
            markup.rows[elem].buttons[0].text = markup.rows[elem].buttons[0].text
    return markup


async def get_keyboard(text_keys: List[str]) -> List[List[Button]]:
    """"""
    keyboard = list()
    for key in range(len(text_keys)):
        keyboard.append([Button.text(text_keys[key], resize=True)])
    return keyboard


async def find_file(pattern: str, path: str) -> List[str]:
    """"""
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


async def is_expected_steps(user_id: int, expected_steps: List[Any]) -> bool:
    """Checking if a user exists in certain steps"""

    current_step = await _get_current_user_step(user_id)

    if current_step in expected_steps:
        return True
    else:
        return False


async def create_img_card(text: str, filename: str) -> None:
    """Create a new card for a word"""

    base_img = Image.open(PATH_IMAGES / "test.png")

    with base_img.copy() as img:
        if len(text) < 15:
            size = 50
        elif 15 <= len(text) <= 20:
            size = 40
        else:
            size = 35
        font = ImageFont.truetype(str(PATH_FONT / "Unbounded-Regular.ttf"), size)
        draw = ImageDraw.Draw(img)
        w, h = 780, 502
        draw.text((w // 2, h // 2), text, font=font, fill="black", anchor="mm")
        img.save(PATH_IMAGES / filename)


async def build_img_cards(words: Dict[str, str]) -> None:
    """"""

    for word, word_ru in words.items():
        await create_img_card(word.lower(), f"{word.replace(' ', '').lower()}_en.png")
        await create_img_card(word_ru.lower(), f"{word.replace(' ', '').lower()}_ru.png")

    return


async def get_proposal_topics(topics: List[str], states: Optional[List[str]] = None) -> List[List[Button]]:
    """"""
    if states is None:
        buttons = [[Button.inline(text=topic, data=topic)] for topic in topics]
    else:
        buttons = [[Button.inline(text=topic + " " + state, data=topic)] for topic, state in zip(topics, states)]

    return buttons


async def build_markup(topics: List[str], current_state: List[str]) -> List[List[Button]]:
    """"""
    markup = [
        [
            Button.inline(text=topics[i] + current_state[i], data=topics[i])
        ] for i in range(len(topics))
    ]

    return markup


async def get_state_markup(markup: Any, user_id: int) -> List[str]:
    """Forming buttons and their states for the user"""

    state = list()

    for row in range(len(markup.rows)):
        text = markup.rows[row].buttons[0].text
        state.append('✅' if '✅' in text else "")

    await _update_user_states(user_id, "states", state)

    return state


async def match_topics_name(topics: List[str]) -> List[str]:
    """Topic name matching"""

    match_topics = list()
    for topic in topics:
        match_topics.append(TOPICS[topic])
    return match_topics


async def get_diff_between_ts(last_ts: Optional[str]) -> float:
    """Returns the difference between two timestamps in seconds"""

    if last_ts is not None:
        current_time = datetime.now()
        last_ts = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S.%f")

        return (current_time - last_ts).total_seconds()
    else:
        return 1000


async def build_list_of_words(user_topics: List[str], user_level: str) -> List[str]:
    """Building a word list for the user depending on the level"""

    total_words = list()

    if "Beginner" in user_level:
        level_key = "a"
    elif "Intermediate" in user_level:
        level_key = "b"
    else:
        level_key = "c"

    for topic, values in WORDS.items():
        if topic in user_topics:
            total_words.append(values[level_key])

    return random.sample(list(itertools.chain(*total_words)), 10)


async def build_history_message(data: List[Tuple[str, str, str]]) -> List[Dict[str, str]]:
    """"""
    result = list()
    for b in data:
        if b[0] == "user":
            item = {"role": "user", "content": b[2]}
        else:
            item = {"role": "assistant", "content": b[2]}
        result.append(item)

    return result


async def check_exist_img(file_name: str) -> bool:
    """Checking if a file with this name exists"""

    file_path = os.path.join("images", file_name)

    return os.path.isfile(file_path)


async def send_img(
    event: NewMessage.Event,
    buttons: List[List[Button]],
    file_name: str,
    current_word: str,
    lang: str,
    type_action: Literal["send", "edit"]
) -> None:
    """Sending an image"""

    if await check_exist_img(file_name):
        if type_action == "send":
            await event.client.send_message(event.chat_id, buttons=buttons,
                                            file=f"/{PATH_IMAGES}/{file_name}")
        elif type_action == "edit":
            await event.client.edit_message(event.sender_id, event.original_update.msg_id,
                                            file=f"/{PATH_IMAGES}/{file_name}",
                                            buttons=buttons)
        else:
            raise ValueError(f"Invalid action type: {type_action}. Expected 'send' or 'edit'.")
    else:
        await create_img_card(current_word.lower(), file_name)
        if type_action == "send":
            await event.client.send_message(event.chat_id, buttons=buttons,
                                            file=f"/{PATH_IMAGES}/{file_name}")
        elif type_action == "edit":
            await event.client.edit_message(event.sender_id, event.original_update.msg_id,
                                            file=f"/{PATH_IMAGES}/{file_name}",
                                            buttons=buttons)
        else:
            raise ValueError(f"Invalid action type: {type_action}. Expected 'send' or 'edit'.")
    return


async def get_translate_word(word: str, from_lang: str) -> str:
    """Translation of a word from a dictionary"""

    if from_lang == "en":
        return TRANSLATES[word]
    else:
        raise ValueError(f"It is impossible to translate into this language")


async def get_code_fill_form(user_id: int) -> int:
    """Returns a status code depending on the availability of data"""

    user_topics = await get_user_topics_db(user_id)
    user_level = await get_user_level_db(user_id)
    user_words = await _get_user_words(user_id)
    if not user_topics and not user_level:
        return -1
    elif not user_topics:
        return -2
    elif not user_level:
        return -3
    elif not user_words:
        return -4
    return 0
