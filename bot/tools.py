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

from db_tools import _update_user_states, _get_current_user_step
from globals import TOPICS, WORDS, TRANSLATES


PATH_IMAGES = Path(__file__).parent.parent.resolve() / "data" / "images"
PATH_FONT = Path(__file__).parent.parent.resolve() / "data"


async def update_text_from_state_markup(markup, state, topics, name):
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


async def get_keyboard(text_keys: list) -> list:
    """"""
    keyboard = list()
    for key in range(len(text_keys)):
        keyboard.append([Button.text(text_keys[key], resize=True)])
    return keyboard


async def find_file(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


async def is_expected_steps(user_id: int, expected_steps: list) -> bool:
    """Checking if a user exists in certain steps"""
    current_step = await _get_current_user_step(user_id)

    if current_step in expected_steps:
        return True
    else:
        return False


async def get_text_from_link(url: str):
    """"""
    response = requests.get(url)
    return response.text


async def create_img_card(text, filename):
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


async def build_img_cards(words):
    print("build_img_cards")

    for word, word_ru in words.items():
        await create_img_card(word.lower(), f"{word.replace(' ', '').lower()}_en.png")
        await create_img_card(word_ru.lower(), f"{word.replace(' ', '').lower()}_ru.png")

    return


async def get_proposal_topics(topics, states=None):
    """"""
    if states is None:
        buttons = [[Button.inline(text=topic, data=topic)] for topic in topics]
    else:
        buttons = [[Button.inline(text=topic + " " + state, data=topic)] for topic, state in zip(topics, states)]

    return buttons


async def build_markup(topics, current_state):
    """"""
    markup = [
        [
            Button.inline(text=topics[i] + current_state[i], data=topics[i])
        ] for i in range(len(topics))
    ]

    return markup


async def get_state_markup(markup, user_id):
    """Forming buttons and their states for the user"""
    state = list()

    for row in range(len(markup.rows)):
        text = markup.rows[row].buttons[0].text
        state.append('✅' if '✅' in text else "")

    await _update_user_states(user_id, "states", state)

    return state


async def match_topics_name(topics: list) -> list:
    """Topic name matching"""
    match_topics = list()
    for topic in topics:
        match_topics.append(TOPICS[topic])
    return match_topics


async def get_diff_between_ts(last_ts):
    """"""
    if last_ts is not None:
        current_time = datetime.now()
        last_ts = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S.%f")

        return (current_time - last_ts).total_seconds()
    else:
        return 1000


async def build_list_of_words(user_topics: list, user_level: str):
    """"""
    total_words = list()
    print(user_topics, user_level)

    if "Beginner" in user_level:
        level_key = "a"
    elif "Intermediate" in user_level:
        level_key = "b"
    else:
        level_key = "c"

    for topic, values in WORDS.items():
        if topic in user_topics:
            total_words.append(values[level_key])

    print(total_words)

    return random.sample(list(itertools.chain(*total_words)), 10)


async def build_history_message(data):
    """"""
    result = list()
    for b in data:
        print("b", b)
        if b[0] == "user":
            item = {"role": "user", "content": b[2]}
        else:
            item = {"role": "assistant", "content": b[2]}
        result.append(item)

    return result


async def check_exist_img(file_name: str):
    """"""
    file_path = os.path.join("images", file_name)

    return os.path.isfile(file_path)


async def send_img(
    event,
    buttons,
    file_name,
    current_word,
    lang,
    type_action
):
    """"""

    if await check_exist_img(file_name):
        print("exist")
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
        print("not exist")
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


async def get_translate_word(word: str, from_lang: str):
    """"""
    if from_lang == "en":
        return TRANSLATES[word]
    else:
        raise ValueError(f"It is impossible to translate into this language")
