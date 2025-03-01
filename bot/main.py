import ast
import os
import sys

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
    get_text_from_link, build_img_cards, get_proposal_topics, build_markup, get_state_markup, \
    match_topics_name, get_diff_between_ts, build_list_of_words, build_history_message, send_img, check_exist_img, \
    create_img_card, get_translate_word

from db import is_user_exist_db, update_data_users_db, update_data_topics_db, get_user_topics_db, \
    get_user_words_db, update_user_words_db, get_user_level_db, update_user_level_db, \
    update_messages_db, update_reviews_db, update_data_events_db, get_event_from_db, get_stat_use_message_db, \
    get_stat_use_link_db, get_history_chat_ellie_db, get_stat_use_mode_db, \
    get_private_db, get_user_for_notify_reviews_db, get_last_message_ellie_db, get_num_translates_db

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config')
config_path = os.path.abspath(config_path)
sys.path.insert(1, config_path)

import config


api_id = config.app_id
api_hash = config.api_hash
bot_token = config.bot_token
test_user_id = config.test_user_id

PATH_IMAGES = Path(__file__).parent.parent.resolve() / "data" / "images"

bot = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

print(bot)

history_dict = dict()


@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    print(event)
    sender_info = await event.get_sender()
    user_id = event.message.peer_id.user_id
    await _create_db()
    await _update_current_user_step(user_id, 0)
    if not await is_user_exist_db(user_id):
        await update_data_users_db(sender_info)

    keyboard = await get_keyboard(["Начать 🚀", "Обо мне 👾"])
    text = "Hi! 👋\n\nРад, что тебе интересно изучение английского языка! " \
           "С Wordbi ты сможешь качественно расширить свой vocabulary. \n\nХороший объем словарного запаса " \
           "поможет читать книги, смотреть любимые фильмы в оригинале и более эффективно " \
           "и уверенно использовать язык в жизни 😉"
    await event.client.send_message(event.chat_id, text, buttons=keyboard)
    await update_data_events_db(user_id, "start", {"step": 0})
    return


@bot.on(events.NewMessage(pattern="Начать 🚀"))
async def begin(event):
    user_id = event.message.peer_id.user_id

    if await is_expected_steps(user_id, [0]):
        await _update_current_user_step(user_id, 1)
        total_topics = list(TOPICS.keys())

        await _update_user_states(user_id, "topics", total_topics)
        await _update_user_states(user_id, "states", ["" for _ in range(len(total_topics))])

        proposal_topics = await match_topics_name(total_topics)
        markup = bot.build_reply_markup(await get_proposal_topics(proposal_topics))

        await get_state_markup(markup, user_id)

        await event.client.send_message(event.chat_id, "Выбери темы, которые тебе могут быть интересны 🐥\n\n"
                                                       "Я буду учитывать их при формировании списка карточек слов для "
                                                       "тебя, а Ellie AI постарается учесть твои интересы в "
                                                       "общении с ней 💜", buttons=markup)
        keyboard = await get_keyboard(["Подтвердить", "Назад"])
        await event.client.send_message(event.sender_id, "Когда закончишь с выбором, жми на Подтвердить!",
                                        buttons=keyboard)
        await update_data_events_db(user_id, "begin", {"step": 1})
    elif await is_expected_steps(user_id, [2]):
        await _update_current_user_step(user_id, 1)

        current_topics = await _get_user_states(user_id, "topics")
        current_state = await _get_user_states(user_id, "states")
        current_topics = await match_topics_name(current_topics)

        markup = bot.build_reply_markup(await get_proposal_topics(current_topics, current_state))
        await get_state_markup(markup, user_id)

        await event.client.send_message(event.chat_id, "Выбери темы, которые тебе могут быть интересны 🐥\n\n"
                                                       "Я буду учитывать их при формировании списка карточек слов для "
                                                       "тебя, а Ellie AI постарается учесть твои интересы в "
                                                       "общении с ней 💜", buttons=markup)
        keyboard = await get_keyboard(["Подтвердить", "Назад"])
        await event.client.send_message(event.sender_id, "Когда закончишь с выбором, жми на Подтвердить!",
                                        buttons=keyboard)
        await update_data_events_db(user_id, "begin", {"step": 2})
    else:
        pass
    return


@bot.on(events.CallbackQuery())
async def handler(event):
    user_id = event.original_update.user_id
    step = await _get_current_user_step(user_id)

    async def process_refresh(event, user_id):
        state = await _get_user_words(user_id)
        current_topic = state[0][0]
        current_word = state[0][1]
        current_lang = state[0][2]

        buttons = [
            [
                Button.inline(text="⬅️", data=-1),
                Button.inline(text="🔄", data=0),
                Button.inline(text="➡️", data=1),
            ],
        ]

        user_self_words = await _get_user_self_words(user_id)

        if current_lang == "ru":
            lang = "en"
        else:
            lang = "ru"

        if lang == "ru":
            try:
                current_word_new = await get_translate_word(word=current_word, from_lang="en")
            except:
                current_word_new = next((v for k, v in user_self_words.items() if k.lower() == current_word.lower()), None)
        else:
            current_word_new = current_word

        await send_img(
            event=event,
            buttons=buttons,
            file_name=f"{current_word.replace(' ', '')}_{lang}.png",
            current_word=current_word_new,
            lang=lang,
            type_action="edit"
        )

        await _update_user_words(user_id, "sport", current_word, lang)
        await update_data_events_db(user_id, "refresh_card", {"step": step})
        return

    async def process_forward(event, user_id):
        if await is_expected_steps(user_id, [50]):
            words_list = await get_user_words_db(user_id)

            words_list = words_list[0]
            state = await _get_user_words(user_id)
            current_word = state[0][1].lower()
            new_current_word = current_word
        else:
            state = await _get_user_words(user_id)
            current_word = state[0][1]

            words_list = await _get_user_self_words(user_id)
            new_current_word = current_word

        for i in range(len(words_list) - 1):
            if words_list[i].lower() == current_word.lower():
                new_current_word = words_list[i + 1].lower()

        if new_current_word == current_word:
            buttons = [
                [
                    Button.inline(text="⬅️", data=-1),
                    Button.inline(text="🔄", data=0),
                ],
            ]
            await send_img(
                event=event,
                buttons=buttons,
                file_name=f"{current_word.replace(' ', '')}_en.png",
                current_word=current_word,
                lang="en",
                type_action="edit"
            )

            keyboard = await get_keyboard(["Проверить себя 🧠", "Завершить"])
            text = "Карточки закончились, но ты можешь продолжать их листать и переворачивать, " \
                   "а также можешь проверить свои знания по кнопке Проверить себя 🧠\n"
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "complete_card", {"step": -1})

        else:
            current_word = new_current_word
            buttons = [
                [
                    Button.inline(text="⬅️", data=-1),
                    Button.inline(text="🔄", data=0),
                    Button.inline(text="➡️", data=1),
                ],
            ]
            await send_img(
                event=event,
                buttons=buttons,
                file_name=f"{current_word.replace(' ', '')}_en.png",
                current_word=current_word,
                lang="en",
                type_action="edit"
            )

            await _update_user_words(user_id, "sport", current_word, "en")
            await update_data_events_db(user_id, "forward_card", {"step": step})
        return

    async def process_backward(event, user_id):
        if await is_expected_steps(user_id, [50]):
            words_list = await get_user_words_db(user_id)
            words_list = words_list[0]
            state = await _get_user_words(user_id)
            current_word = state[0][1]
            current_word = current_word.lower()
            new_current_word = current_word
        else:
            state = await _get_user_words(user_id)
            current_word = state[0][1]
            words_list = await _get_user_self_words(user_id)
            new_current_word = current_word

        for i in range(1, len(words_list)):
            if words_list[i].lower() == current_word.lower():
                new_current_word = words_list[i - 1].lower()
        if new_current_word == current_word:
            buttons = [
                [
                    Button.inline(text="🔄", data=0),
                    Button.inline(text="➡️", data=1),
                ],
            ]
            await send_img(
                event=event,
                buttons=buttons,
                file_name=f"{current_word.replace(' ', '')}_en.png",
                current_word=current_word,
                lang="en",
                type_action="edit"
            )

            await update_data_events_db(user_id, "backward_card_first", {"step": step})
        else:
            current_word = new_current_word

            buttons = [
                [
                    Button.inline(text="⬅️", data=-1),
                    Button.inline(text="🔄", data=0),
                    Button.inline(text="➡️", data=1),
                ],
            ]
            await send_img(
                event=event,
                buttons=buttons,
                file_name=f"{current_word.replace(' ', '')}_en.png",
                current_word=current_word,
                lang="en",
                type_action="edit"
            )

            await _update_user_words(user_id, "sport", current_word, "en")
            await update_data_events_db(user_id, "backward_card", {"step": step})
        return

    async def gather_user_states(user_id):
        current_topics = await _get_user_states(user_id, "topics")
        current_state = await _get_user_states(user_id, "states")
        current_topics = await match_topics_name(current_topics)
        return current_topics, current_state

    async def process_button_click(event, user_id, data_filter):
        if data_filter == "🔄":
            await process_refresh(event, user_id)
        elif data_filter in ["➡️", "1"]:
            await process_forward(event, user_id)
        elif data_filter in ["⬅️", "-1"]:
            await process_backward(event, user_id)

    async def handle_expected_steps_6_1(event, user_id):
        current_topics, current_state = await gather_user_states(user_id)
        topic_clicked = event.data.split(b'$')[0].decode("utf-8")

        markup = bot.build_reply_markup(await build_markup(current_topics, current_state))
        await update_text_from_state_markup(markup, current_state, current_topics, topic_clicked)
        await get_state_markup(markup, user_id)
        await event.client.edit_message(event.sender_id, event.message_id, buttons=markup)

    async def handle_expected_step_9(event, user_id):
        data_filter = event.data.decode("utf-8")

        if data_filter in ["🔄", "➡️", "1", "⬅️", "-1"]:
            await process_button_click(event, user_id, data_filter)

    async def get_cards(event):
        data_filter = event.data.decode("utf-8")

        if data_filter == "10":
            await get_start_cards(event)
        else:
            user_words = await get_user_words_db(user_id)
            user_words = user_words[0]
            if user_words:
                await _update_current_user_step(user_id, 901)
                await get_start_cards(event)
            else:
                text = "Кажется, еще не добавлены карточки по ссылке. Добавим?"
                keyboard = await get_keyboard(["Создать свой набор слов", "Завершить"])
                await event.client.send_message(event.chat_id, text, buttons=keyboard)

    if await is_expected_steps(user_id, [1, 2]):
        await handle_expected_steps_6_1(event, user_id)
    elif await is_expected_steps(user_id, [51, 501, 50]):
        await handle_expected_step_9(event, user_id)
    elif await is_expected_steps(user_id, [545]):
        await get_cards(event)
    elif await is_expected_steps(user_id, [2011, 2010]):
        data_filter = event.data.decode("utf-8")
        if data_filter == "56":
            if await is_expected_steps(user_id, [2010]):
                await _update_current_user_step(user_id, 3010)
                await testing_words(event)
            elif await is_expected_steps(user_id, [2011]):
                await _update_current_user_step(user_id, 3011)
                await testing_words(event)
    elif await is_expected_steps(user_id, [61, 62]):
        data_filter = event.data.decode("utf-8")
        if data_filter == "49":
            last_message = await get_last_message_ellie_db(user_id)
            await update_data_events_db(user_id, "translate_message", {"step": step})
            if last_message:
                last_message = last_message[0]
                translated_text = await get_translate(user_id, last_message)
                num_translates = await get_num_translates_db(user_id)

                if num_translates is None or num_translates == 0:
                    translated_text += ">\n\nСтарайся отвечать на английском языке! Регулярное общение поможет приобрести или " \
                                       "закрепить навык формулирования предложений и сделает более эффективным запоминание слов 🤓"
                keyboard = await get_keyboard(["Завершить"])
                await event.client.send_message(event.chat_id, "<" + translated_text + ">", buttons=keyboard)
                await update_data_events_db(user_id, "translate_message_success", {"step": step})


@bot.on(events.NewMessage(pattern="Подтвердить"))
async def confirmed(event):
    user_id = event.message.peer_id.user_id
    if await is_expected_steps(user_id, [1, 2, 3]):
        step = await _get_current_user_step(user_id)
        await _update_current_user_step(user_id, 2)
        current_topics = await _get_user_states(user_id, "topics")
        current_states = await _get_user_states(user_id, "states")

        chooses_topic = list()

        for state, topic in zip(current_states, current_topics):
            if state != "":
                chooses_topic.append(topic)

        if len(chooses_topic) != 0:
            await update_data_topics_db(user_id, chooses_topic)

            keyboard = await get_keyboard(["A1-A2: Beginner 💫", "B1-B2: Intermediate ⭐️", "C1-C2: Advanced 🌟", "Назад"])
            text = "Выбери наиболее подходящий для тебя уровень языка 📚\n\nЭто поможет мне " \
                   "сформировать еще более точную персональную подборку слов для тебя 🫶"
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "success", {"step": step})
            await _update_user_choose_topic(user_id, sorted(chooses_topic))

        else:
            text = "Не выбрано ни одной темы..🦦"
            keyboard = await get_keyboard(["Подтвердить"])
            await event.client.send_message(event.chat_id, text, buttons=keyboard)
            await update_data_events_db(user_id, "success", {"step": step, "error": "no_topics"})
    else:
        pass
    return


async def filter_levels(event):
    """"""
    user_id = event.message.peer_id.user_id

    if event.message.message in ("A1-A2: Beginner 💫", "B1-B2: Intermediate ⭐️", "C1-C2: Advanced 🌟"):
        await update_user_level_db(user_id, event.message.message)
        return True
    else:
        return False


@bot.on(events.NewMessage(func=filter_levels))
async def choose_level(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [2, 41, 42]):
        await _update_current_user_step(user_id, 3)
        keyboard = await get_keyboard(["Карточки слов 🧩", "Чат с Ellie 💬", "Назад"])
        text = "Ты можешь выбрать один из двух режимов:\n\n1️⃣ Карточки слов 🧩: в этом режиме я сформирую для тебя список " \
               "слов для изучения на основе твоих интересов и текущего уровня языка или ты можешь отправить мне свои " \
               "интересы, а я сформирую на их основе список " \
               "слов. Тогда пополнить словарный запас по твоим любимым темам будет очень просто!\n\n2️⃣ Чат с Ellie AI 💬: с " \
               "ней можно сыграть в игру Quiz me или просто поболтать 🙂"
        await event.client.send_message(event.sender_id, text,
                                        buttons=keyboard)
        await update_data_events_db(user_id, "choose_level", {"step": step, "level": event.message.message})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Карточки слов 🧩"))
async def cards(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [3, 51, 52, 9]):
        await _update_current_user_step(user_id, 41)
        keyboard = await get_keyboard([
            "Карточки на основе интересов 👾",
            "Создать свой набор слов 🧬",
            "Назад"
        ])
        text = "Создать набор карточек на основе твоих интересов или хочешь создать свой набор слов? \n\n" \
               "👾 Карточки на основе интересов - я создам карточки на основе интересов, которые ты уже выбрал\n" \
               "🧬 Создать свой набор слов - в этом " \
               "режиме я автоматически сгенерирую карточки на основе тем, которые ты мне пришлешь 🤓\n\n"
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "cards", {"step": step})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Карточки на основе интересов 👾"))
async def get_start_cards(event):
    try:
        user_id = event.message.peer_id.user_id
    except:
        user_id = event.original_update.user_id

    step = await _get_current_user_step(user_id)
    print("step", step)

    if await is_expected_steps(user_id, [41, 101, 501, 901, 545]):
        print("if await is_expected_steps(user_id, [41, 101, 501, 901, 545])")

        topics = await get_user_topics_db(user_id)
        user_level = await get_user_level_db(user_id)

        if await is_expected_steps(user_id, [901]):
            words_list = await get_user_words_db(user_id)
            words_list = words_list[0]
            await _update_current_user_step(user_id, 50)
            current_word = words_list[0].lower()

        else:
            print("words_list = await build_list_of_words(topics, user_level)")
            words_list = await build_list_of_words(topics, user_level)
            await _update_user_self_words(user_id, words_list)
            current_word = (words_list[0]).lower()
            await _update_current_user_step(user_id, 51)
        print("word_list", words_list, current_word)

        buttons = [
            [
                Button.inline(text="⬅️", data=-1),
                Button.inline("🔄", data=0),
                Button.inline("➡️", data=1),
            ],
        ]

        keyboard = await get_keyboard(["Проверить себя 🧠", "Завершить"])
        text = "Сформировал для тебя набор слов, начнем? ☄️\n\n" \
               "Как пользоваться карточками?\n\n" \
               "➡️ - листать вперед\n🔄 - перевернуть карточку (показать перевод)\n⬅️ - листать назад\n\n" \
               "Проверить себя🧠 - нажимай, если захочешь проверить свои знания!\n\n" \
               "А если устанешь или надоест, можно закончить, нажав на кнопку Завершить\n\n"

        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await send_img(
            event=event,
            buttons=buttons,
            file_name=f"{current_word.replace(' ', '')}_en.png",
            current_word=current_word,
            lang="en",
            type_action="send"
        )

        await _update_user_words(user_id, "sport", current_word, "en")
        await update_data_events_db(user_id, "cards_interests", {"step": step})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Создать свой набор слов 🧬"))
async def create_self_words(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [41, 545]):
        await _update_current_user_step(user_id, 52)

        text = "Отправь мне тему или сразу несколько тем, и я сгенерирую карточки по выбранным тобой темам. " \
               "Твой уровень языка тоже учту 🤗\n\nНапример: IT, Химия или Домашние животные\n\n" \
               ""

        await event.client.send_message(event.chat_id, text, buttons=Button.clear())
        await update_data_events_db(user_id, "create_words", {"step": step})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Чат с Ellie 💬"))
async def start_chat(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [3, 6, 9]):
        await _update_current_user_step(user_id, 42)
        keyboard = await get_keyboard(["Quiz me 📝", "Поболтать 💌", "Назад"])
        text = "Выбери один из двух режимов:\n\nQuiz me 📝 - в этом режиме Ellie AI будет спрашивать у тебя значения " \
               "слов, которые я тебе подобрал на основе твоих интересов, а твоя задача объяснить их значение. На " \
               "английском языке, конечно же 😏\n\nА если просто хочешь поболтать с Ellie AI, то выбирай режим Поболтать 💌\n" \
               "Ellie учтет твои интересы и уровень языка 😉"
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "chat", {"step": step})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Quiz me 📝"))
async def get_begin(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    cnt_uses = await get_stat_use_mode_db(user_id)
    if cnt_uses < LIMIT_USES or cnt_uses is None or user_id == test_user_id:
        if await is_expected_steps(user_id, [42]):
            await _update_current_user_step(user_id, 61)
            keyboard = await get_keyboard(["Завершить"])

            level = await get_user_level_db(user_id)
            words_list = await _get_user_self_words(user_id)

            async with event.client.action(user_id, "typing"):
                text = await get_response(user_id=user_id, history="", message="", words=words_list, level=level)
                print("text", text)

            buttons = [
                [
                    Button.inline(text="Перевести", data=49),
                ],
            ]
            await event.client.send_message(event.chat_id, text, buttons=buttons, reply_to=event.message.id)
            await update_messages_db(user_id, "quiz", "ellie", "user", text.replace("'", ""))
            await update_data_events_db(user_id, "quiz_me", {"step": step})
        else:
            pass
    else:
        await event.client.send_message(event.chat_id, "Слишком много запросов за сегодня 🙂")
        await update_data_events_db(user_id, "quiz_me_error", {"step": -1, "error": "limit"})
    return


@bot.on(events.NewMessage(pattern="Поболтать 💌"))
async def get_begin(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)
    last_ts_event = await get_event_from_db(user_id, "talking")
    if last_ts_event is None or await get_diff_between_ts(str(last_ts_event)) > LIMIT_TIME_EVENTS:
        cnt_uses = await get_stat_use_mode_db(user_id)
        if cnt_uses < LIMIT_USES or cnt_uses is None or user_id == test_user_id:
            if await is_expected_steps(user_id, [42]):
                await _update_current_user_step(user_id, 62)
                keyboard = await get_keyboard(["Завершить"])

                topics = await get_user_topics_db(user_id)
                level = await get_user_level_db(user_id)
                words_list = await _get_user_self_words(user_id)

                async with event.client.action(user_id, "typing"):
                    text = await get_conversations(user_id=user_id, history="",
                                                   message="", words=words_list, topics=topics, level=level)
                buttons = [
                    [
                        Button.inline(text="Перевести", data=49),
                    ],
                ]
                await event.client.send_message(event.chat_id, text, buttons=buttons, reply_to=event.message.id)
                await update_messages_db(user_id, "conversation", "ellie", "user", text.replace("'", ""))
                await update_data_events_db(user_id, "talking", {"step": step})
            else:
                pass
        else:
            await event.client.send_message(event.chat_id, "Слишком много запросов за сегодня 🙂")
            await update_data_events_db(user_id, "conversation_error", {"step": -1, "error": "limit"})
    else:
        await event.client.send_message(event.chat_id, "Слишком частые запросы!\n\nПопробуй "
                                                       "через несколько минут 🙂")
        await update_data_events_db(user_id, "talking", {"step": step, "error": "flood"})
    return


@bot.on(events.NewMessage())
async def get_begin(event):
    user_id = event.message.peer_id.user_id
    if await is_expected_steps(user_id, [61, 62]) and event.message.message not in ("Quiz me 📝", "Поболтать 💌",
                                                                                    "Завершить", "Проверить себя 🧠",
                                                                                    "Создать свой набор слов 🧬"):
        if event.message.message not in ("/start", "/my_cards", "/interests", "/level", "/reviews"):
            keyboard = await get_keyboard(["Завершить"])

            topics = await get_user_topics_db(user_id)
            level = await get_user_level_db(user_id)
            words_list = await _get_user_self_words(user_id)

            last_ts_event_quiz = await get_event_from_db(user_id, "message_from_user_quiz")
            last_ts_event_conv = await get_event_from_db(user_id, "message_from_user_conv")
            if last_ts_event_quiz is None or await get_diff_between_ts(str(last_ts_event_quiz)) > LIMIT_TIME_EVENTS or \
                    last_ts_event_conv is None or await get_diff_between_ts(str(last_ts_event_conv)) > LIMIT_TIME_EVENTS \
                    or user_id == test_user_id:

                cnt_uses = await get_stat_use_message_db(user_id)
                if cnt_uses < LIMIT_USES_MESSAGES or cnt_uses is None or user_id == test_user_id:
                    if await is_expected_steps(user_id, [61]):
                        await update_messages_db(user_id, "quiz", "user", "ellie", (event.message.message).replace("'", ""))
                        await update_data_events_db(user_id, "message_from_user_quiz", {"step": -1})
                        messages_history = await get_history_chat_ellie_db(user_id, "quiz")
                        if not messages_history:
                            messages_history = []
                        else:
                            messages_history = await build_history_message(messages_history)
                        async with event.client.action(user_id, "typing"):

                            text = await get_response(user_id=user_id, history=messages_history,
                                                      message=event.message.message, words=words_list, level=level)
                            if text:
                                await update_messages_db(user_id, "quiz", "ellie", "user", text.replace("'", ""))
                                buttons = [
                                    [
                                        Button.inline(text="Перевести", data=49),
                                    ],
                                ]
                                await event.client.send_message(event.chat_id, text, reply_to=event.message.id, buttons=buttons)
                                await update_data_events_db(user_id, "message_to_user_quiz", {"step": -1})
                            else:
                                keyboard = await get_keyboard(["Завершить"])
                                text = "Что-то сломалось 😣\n\nУже чиним, попробуй позже"
                                await event.client.send_message(event.chat_id, text, buttons=keyboard)
                    else:
                        await update_messages_db(user_id, "conversation", "user", "ellie", event.message.message)
                        await update_data_events_db(user_id, "message_from_user_conv", {"step": -1})
                        messages_history = await get_history_chat_ellie_db(user_id, "conversation")
                        if not messages_history:
                            messages_history = []
                        else:
                            messages_history = await build_history_message(messages_history)
                        async with event.client.action(user_id, "typing"):
                            text = await get_conversations(user_id=user_id, history=messages_history,
                                                           message=event.message.message, words=words_list, topics=topics,
                                                           level=level)
                            if text:
                                await update_messages_db(user_id, "conversation", "ellie", "user", text.replace("'", ""))
                                buttons = [
                                    [
                                        Button.inline(text="Перевести", data=49),
                                    ],
                                ]
                                await event.client.send_message(event.chat_id, text, reply_to=event.message.id, buttons=buttons)
                                await update_data_events_db(user_id, "message_to_user_conv", {"step": -1})
                            else:
                                keyboard = await get_keyboard(["Завершить"])
                                text = "Что-то сломалось 😣\n\nУже чиним, попробуй позже"
                                await event.client.send_message(event.chat_id, text, buttons=keyboard)
                else:
                    await event.client.send_message(event.chat_id, "Слишком много запросов за сегодня 🙂")
                    await update_data_events_db(user_id, "message_from_user_error", {"step": -1, "error": "limit"})
            else:
                await event.client.send_message(event.chat_id, "Слишком частые запросы!\n\nПопробуй "
                                                               "через несколько минут 🙂")
                await update_data_events_db(user_id, "message_from_user_error", {"step": -1, "error": "flood"})
        else:
            keyboard = await get_keyboard(["Завершить"])
            text = "Чтобы воспользоваться командами из меню, необходимо закончить диалог с Ellie по кнопке Завершить 🙂"
            await event.client.send_message(event.chat_id, text, reply_to=event.message.id, buttons=keyboard)

    elif await is_expected_steps(user_id, [2011]) and event.message.message not in ("Quiz me 📝", "Поболтать 💌",
                                                                                    "Завершить", "Проверить себя 🧠",
                                                                                    "Создать свой набор слов 🧬"):
        if event.message.message not in ("/start", "/my_cards", "/interests", "/level", "/reviews"):
            cur_test_word = await _get_user_test_words(user_id)
            user_words = await get_user_words_db(user_id)
            user_words_en = user_words[0]
            user_words_ru = user_words[1]
            words_test = dict()
            for en, ru in zip(user_words_en, user_words_ru):
                words_test[en.lower()] = ru.lower()

            keyboard = await get_keyboard(["Завершить"])
            if words_test[cur_test_word.lower()] == event.message.message.lower():
                await event.client.send_message(event.chat_id, "Иии..верно! Так держать 🦾", reply_to=event.message.id, buttons=keyboard)
                await update_data_events_db(user_id, "testing_success",
                                            {"step": -1, "word": event.message.message.lower()})
                await _update_current_user_step(user_id, 3011)
                await testing_words(event)
            else:
                buttons = [
                    [
                        Button.inline(text="Пропустить", data=56),
                    ],
                ]
                await event.client.send_message(event.chat_id, "Неверно 🙁 попробуй еще раз!", reply_to=event.message.id,
                                                buttons=buttons)
                await update_data_events_db(user_id, "testing_failed",
                                            {"step": -1, "word": event.message.message.lower()})
        else:
            keyboard = await get_keyboard(["Завершить"])
            text = "Чтобы воспользоваться командами из меню, необходимо закончить проверку себя по кнопке Завершить 🙂"
            await event.client.send_message(event.chat_id, text, reply_to=event.message.id, buttons=keyboard)
    elif await is_expected_steps(user_id, [2010]) and event.message.message not in ("Quiz me 📝", "Поболтать 💌",
                                                                                    "Завершить", "Проверить себя 🧠",
                                                                                    "Создать свой набор слов 🧬"):
        if event.message.message not in ("/start", "/my_cards", "/interests", "/level", "/reviews"):
            cur_test_word = await _get_user_test_words(user_id)
            user_words_en = await _get_user_self_words(user_id)
            user_words_ru = [TRANSLATES[i] for i in user_words_en]
            words_test = dict()

            for en, ru in zip(user_words_en, user_words_ru):
                words_test[en.lower()] = ru.lower()
            keyboard = await get_keyboard(["Завершить"])

            if words_test[cur_test_word.lower()] == event.message.message.lower():
                await event.client.send_message(event.chat_id, "Иии..верно! Так держать 🦾", reply_to=event.message.id, buttons=keyboard)
                await update_data_events_db(user_id, "testing_success", {"step": -1, "word": event.message.message.lower()})
                await _update_current_user_step(user_id, 3010)
                await testing_words(event)
            else:
                buttons = [
                    [
                        Button.inline(text="Пропустить", data=56),
                    ],
                ]
                await event.client.send_message(event.chat_id, "Неверно 🙁 попробуй еще раз!", reply_to=event.message.id,
                                                buttons=buttons)
                await update_data_events_db(user_id, "testing_failed",
                                            {"step": -1, "word": event.message.message.lower()})
        else:
            keyboard = await get_keyboard(["Завершить"])
            text = "Чтобы воспользоваться командами из меню, необходимо закончить проверку себя по кнопке Завершить 🙂"
            await event.client.send_message(event.chat_id, text, reply_to=event.message.id, buttons=keyboard)
    elif await is_expected_steps(user_id, [10]) and event.message.message not in ("Назад", "/reviews", "/interests",
                                                                                  "/level", "/my_cards", "/start"):
        await _update_current_user_step(user_id, 676)
        await update_reviews_db(user_id, event.message.message)
        buttons = [
            [
                Button.url(text="Оставить email", url="https://wordbi.com/#subscribe"),
            ],
        ]
        text = "Спасибо! А если хочешь получить эксклюзивный доступ одним из первых, " \
               "то можешь оставить свой email вот тут: https://wordbi.com/#subscribe"
        await event.client.send_message(event.chat_id, text, buttons=buttons)
        await update_data_events_db(user_id, "success_review", {"step": -1})

    elif await is_expected_steps(user_id, [52]) and event.message.message not in ("Quiz me 📝", "Поболтать 💌",
                                                                                    "Завершить", "Проверить себя 🧠",
                                                                                    "Создать свой набор слов 🧬"):
        last_ts_event = await get_event_from_db(user_id, "message_from_user_conv")
        if last_ts_event is None or await get_diff_between_ts(str(last_ts_event)) > 100:
            cnt_uses = await get_stat_use_link_db(user_id)
            if cnt_uses < LIMIT_LINK_USES or cnt_uses is None or user_id == test_user_id:
                await event.client.send_message(event.chat_id, "Формирую список слов..",
                                                reply_to=event.message.id, buttons=Button.clear())
                try:
                    topics = event.message.message
                    level = await get_user_level_db(user_id)
                    card_words = await build_cards_from_text(topics, level, user_id)
                    if not card_words:
                        keyboard = await get_keyboard(["Завершить"])
                        text = "Что-то сломалось 😣\n\nУже чиним, попробуй позже"
                        await event.client.send_message(event.chat_id, text, buttons=keyboard)
                    elif card_words == "None":
                        keyboard = await get_keyboard(["Завершить"])
                        await event.client.send_message(event.chat_id,
                                                        "Кажется, выбранные темы слишком специфичны 😔\n\n"
                                                        "Попробуй выбрать другие темы 💜",
                                                        buttons=keyboard)
                        await update_data_events_db(user_id, "cards_from_link_error", {"step": -1,
                                                                                       "error": "specific"})
                    else:
                        card_words = ast.literal_eval(card_words)
                        if not isinstance(card_words, dict):
                            keyboard = await get_keyboard(["Завершить"])
                            await event.client.send_message(event.chat_id, "Упс..произошла какая-то ошибка. "
                                                                           "Меня уже чинят, попробуй попозже 💜",
                                                            buttons=keyboard)
                        else:
                            await _update_user_self_words(user_id, card_words)
                            fixed_card_words = dict()
                            for word, translate in card_words.items():
                                fixed_card_words[word.replace('/', '')] = translate.replace('/', '')
                            await build_img_cards(fixed_card_words)
                            keyboard = await get_keyboard(["Увидеть карточки 💜"])
                            await _update_user_words(user_id, "self", "", "en")
                            await _update_user_choose_topic(user_id, "self")
                            await update_user_words_db(user_id, fixed_card_words, event.message.message)
                            await event.client.send_message(event.chat_id, "Чтобы увидеть карточки, жмякай на "
                                                                           "Увидеть карточки 💜",
                                                            buttons=keyboard)
                            await update_data_events_db(user_id, "cards_from_link_success", {"step": -1})
                            await _update_current_user_step(user_id, 101)
                except Exception:
                    keyboard = await get_keyboard(["Завершить"])
                    await event.client.send_message(event.chat_id, "Упс..произошла какая-то ошибка. "
                                                                   "Меня уже чинят, попробуй попозже 💜",
                                                    buttons=keyboard)
                    await update_data_events_db(user_id, "cards_from_link_error",
                                                {"step": -1, "error": "api"})
            else:
                await event.client.send_message(event.chat_id, "Слишком много запросов за сегодня 🙂")
                await update_data_events_db(user_id, "cards_from_link_error", {"step": -1, "error": "limit"})
        else:
            await event.client.send_message(event.chat_id, "Слишком частые запросы!\n\nПопробуй "
                                                           "через несколько минут 🙂")
            await update_data_events_db(user_id, "cards_from_link_error", {"step": -1, "error": "flood"})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Завершить"))
async def get_end(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [52, 101, 61, 62, 51, 41, 2011, 3011, 2010, 3010, 901, 10, 50, 676, 10]):
        await _update_current_user_step(user_id, 7)
        keyboard = await get_keyboard(["Выбрать другой режим ⚙️", "Оставить отзыв 💌"])
        text = "Хорошо! Чтобы вернуться к просмотру карточек слов, выбери в боковом меню команду /my_cards 🙃\n\n" \
               "А здесь ты можешь выбрать другой режим или оставить отзыв 💜"
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "complete", {"step": step})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Увидеть карточки 💜"))
async def get_begin(event):
    user_id = event.message.peer_id.user_id

    if await is_expected_steps(user_id, [101]):
        await _update_current_user_step(user_id, 901)
        await get_start_cards(event)
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Проверить себя 🧠"))
async def testing_words(event):

    async def send_test_word_message(word, step, additional_buttons=[]):
        message_content = "Ура! Это было последнее слово, хороший результат! 😻\n\nЧтобы закончить, нажми на Завершить" \
            if word is None else ""
        if word:
            if await check_exist_img(f"/{PATH_IMAGES}/{word.replace(' ', '')}_en.png"):
                image_file = f"/{PATH_IMAGES}/{word.replace(' ', '')}_en.png"
            else:
                await create_img_card(word.replace(' ', '').lower(), f"/{PATH_IMAGES}/{word.replace(' ', '')}_en.png")
                image_file = f"/{PATH_IMAGES}/{word.replace(' ', '')}_en.png"
        else:
            image_file = None

        if word is not None:
            buttons = [
                [
                    Button.inline(text="Пропустить", data=56),
                ],
            ]
        else:
            buttons = await get_keyboard(["Завершить"])
            await update_data_events_db(user_id, "testing_complete", {"step": -1})

        await event.client.send_message(event.chat_id, message_content, buttons=buttons, file=image_file)
        if word is not None:
            await _update_user_test_words(user_id, word)
        await _update_current_user_step(user_id, step)

    def get_next_test_word(current_word, words_list):
        if current_word in words_list:
            index = words_list.index(current_word)
            return words_list[index + 1] if index + 1 < len(words_list) else None
        return words_list[0]

    try:
        user_id = event.message.peer_id.user_id
    except AttributeError:
        user_id = event.original_update.user_id

    steps_to_categories = [50, 51, 3011, 2011, 3010, 2010, 51, 2010, 3010]

    current_step = await is_expected_steps(user_id, steps_to_categories)
    if current_step:
        step = await _get_current_user_step(user_id)
        if step in [50, 2011, 3011]:
            words_list = await get_user_words_db(user_id)
            words_list = words_list[0]
        else:
            words_list = await _get_user_self_words(user_id)
        cur_test_word = await _get_user_test_words(user_id)

        if not await is_expected_steps(user_id, [3011, 3010]):
            text = "А теперь я буду проверять тебя! 😈 \n\nЯ буду тебе показывать карточку на английском языке, а твоя " \
                   "задача написать мне перевод слова на русском языке, которое было написано с обратной стороны " \
                   "карточки 😊\n\n" \
                   "Если не помнишь слово, нажимай на Пропустить\n" \
                   "А если устанешь или надоест, нажимай на пнопку Завершить"
            await event.client.send_message(event.chat_id, text, buttons=await get_keyboard(["Завершить"]))
            new_cur_test_word = words_list[0]
        else:
            new_cur_test_word = get_next_test_word(cur_test_word, words_list)

        step_update = 2011 if step in [50, 2011, 3011] else 2010
        await send_test_word_message(new_cur_test_word, step_update, [])
        await update_data_events_db(user_id, "testing", {"step": step})


@bot.on(events.NewMessage(pattern="Выбрать другой режим ⚙️"))
async def get_begin(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [7]):
        await _update_current_user_step(user_id, 9)
        keyboard = await get_keyboard(["Карточки слов 🧩", "Чат с Ellie 💬"])
        text = "Попробуем что-то другое? 😏"
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "other_mode", {"step": step})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Оставить отзыв 💌"))
async def leave_feedback(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [7, 8, 898]):
        await _update_current_user_step(user_id, 10)
        keyboard = await get_keyboard(["Назад"])
        text = "Буду очень рад, если поделишься своим впечатлением! Для этого просто отправь мне сообщение 💜"
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "leave_feedback", {"step": step})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="Обо мне 👾"))
async def about_me(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if await is_expected_steps(user_id, [0]):
        await _update_current_user_step(user_id, 11)

        keyboard = await get_keyboard(["Назад"])
        text = "Хэй!\n\nЯ бот, созданный с целью помочь расширить словарный запас. \n\n" \
               "Вместе со мной ты можешь создать карточки слов и пообщаться с Ellie AI, " \
               "которая работает на базе моделей от Open AI 👾"
        await event.client.send_message(event.chat_id, text, buttons=keyboard)
        await update_data_events_db(user_id, "about_me", {"step": step})
    else:
        pass
    return


@bot.on(events.NewMessage(pattern="/my_cards"))
async def get_my_cards(event):
    user_id = event.message.peer_id.user_id
    if not await is_expected_steps(user_id, [3011, 3010, 2011, 2010, 61, 62]):
        step = await _get_current_user_step(user_id)
        await _update_current_user_step(user_id, 545)

        text = "Выбери тип карточек, которые нужно открыть🤗\n\n"

        buttons = [
            [
                Button.inline(text="По интересам", data=10),
                Button.inline(text="Мои карточки", data=11),
            ],
        ]

        await event.client.send_message(event.chat_id, text, buttons=buttons)

        text = "▪️ По интересам - карточки, созданные на основе твоих интересов\n" \
               "▪️ Из ссылки - карточки, созданные из ссылки"
        await event.client.send_message(event.chat_id, text, buttons=Button.clear())

        await update_data_events_db(user_id, "my_cards", {"step": step})
    else:
        pass

    return


async def get_code_fill_form(user_id):
    """Returns a specific user data availability code"""

    user_topics = await get_user_topics_db(user_id)
    user_exist = await is_user_exist_db(user_id)
    user_level = await get_user_level_db(user_id)
    if not user_exist:
        return -1
    elif not user_topics:
        return -2
    elif not user_level:
        return -3
    else:
        return 0


@bot.on(events.NewMessage(pattern="/interests"))
async def get_my_cards(event):
    user_id = event.message.peer_id.user_id
    if not await is_expected_steps(user_id, [3011, 3010, 2011, 2010, 61, 62]):
        step = await _get_current_user_step(user_id)

        await update_data_events_db(user_id, "change_interests", {"step": step})

        if await get_code_fill_form(user_id) == -1:
            await event.client.send_message(event.chat_id,
                                            "Еще не выбраны настройки ☺️\n\nНажимай на /start", buttons=Button.clear())
            await update_data_events_db(user_id, "change_interests", {"step": -1, "error": "without users"})
        elif await get_code_fill_form(user_id) == -2:
            await update_data_events_db(user_id, "change_interests", {"step": -1, "error": "without_interests"})
            await event.client.send_message(event.chat_id, "Еще не выбраны интересы. Сделаем это прямо сейчас? ☺️")
            await _update_current_user_step(user_id, 0)
            await begin(event)

        else:
            await _update_current_user_step(user_id, 2)
            await begin(event)
    else:
        pass

    return


@bot.on(events.NewMessage(pattern="/level"))
async def get_my_cards(event):
    user_id = event.message.peer_id.user_id
    if not await is_expected_steps(user_id, [3011, 3010, 2011, 2010, 61, 62]):
        step = await _get_current_user_step(user_id)

        await update_data_events_db(user_id, "change_level", {"step": step})

        if await get_code_fill_form(user_id) == -1:
            await event.client.send_message(event.chat_id,
                                            "Еще не выбраны настройки ☺️\n\nНажимай на /start", buttons=Button.clear())
            await update_data_events_db(user_id, "change_interests", {"step": -1, "error": "without users"})
        elif await get_code_fill_form(user_id) == -2:
            await update_data_events_db(user_id, "change_interests", {"step": -1, "error": "without_interests"})
            await event.client.send_message(event.chat_id, "Еще не выбраны интересы. Сделаем это прямо сейчас? ☺️")
            await _update_current_user_step(user_id, 0)
            await begin(event)
        else:
            await _update_current_user_step(user_id, 2)
            await confirmed(event)
    else:
        pass

    return


@bot.on(events.NewMessage(pattern="/reviews"))
async def get_reviews(event):
    user_id = event.message.peer_id.user_id

    if not await is_expected_steps(user_id, [3011, 3010, 2011, 2010, 61, 62]):
        step = await _get_current_user_step(user_id)
        await _update_current_user_step(user_id, 898)
        await update_data_events_db(user_id, "reviews", {"step": step})
        await leave_feedback(event)
    else:
        pass

    return


@bot.on(events.NewMessage(pattern="/fiton"))
async def get_fiton(event):
    """"""
    user_id = event.message.peer_id.user_id

    if user_id == test_user_id:
        chats = await get_user_for_notify_reviews_db()

        if chats:
            text = "Псс..Я заметил, что ты уже пользовался функционалом. Буду рад, если оставишь отзыв 💜\n\n" \
                   "Напомню, чтобы оставить отзыв, можно воспользоваться командой /reviews\n"
            for chat in chats:
                await event.client.send_message(chat, text, buttons=Button.clear())
            await update_data_events_db(user_id, "send_notify_reviews", {"step": -1, "data": chats})
        else:
            pass
    else:
        pass

    return


@bot.on(events.NewMessage(pattern="/deloss"))
async def get_delos(event):
    """"""
    user_id = event.message.peer_id.user_id

    if user_id == test_user_id:
        data = await get_private_db()

        if data:
            total_users = data[0]
            users_ellie = data[1]
            users_cards = data[2]
            users_reviews = data[3]
            text = "Приветики\n\nОсновная статистика: \n\n" \
                   f"Всего пользователей: {total_users}\n" \
                   f"Воспользовались чатом: {users_ellie}\n" \
                   f"Воспользовались карточками: {users_cards}\n" \
                   f"Оставили отзыв: {users_reviews}\n\n<3"
            await event.client.send_message(event.chat_id, text, buttons=Button.clear())
            await update_data_events_db(user_id, "download_stats", {"step": -1, "data": data})
        else:
            pass
    else:
        pass

    return


@bot.on(events.NewMessage(pattern="Назад"))
async def get_back(event):
    """"""
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
    elif await is_expected_steps(user_id, [10]):
        await get_end(event)
    elif await is_expected_steps(user_id, [676]):
        await get_end(event)
    elif await is_expected_steps(user_id, [62]):
        await get_end(event)

    return


bot.run_until_disconnected()
