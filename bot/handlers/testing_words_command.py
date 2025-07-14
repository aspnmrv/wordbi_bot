from telethon import events, Button
import json
import random

from bot.tools import get_keyboard, check_exist_img, create_img_card, is_expected_steps
from bot.db_tools import (
    _get_current_user_step,
    _update_current_user_step,
    _update_user_test_words,
    _get_user_test_words,
    _get_user_self_words,
    _get_user_choose_category,
    _update_user_main_mode,
    _get_user_main_mode,
    _get_user_test_sequence,
    _update_user_test_sequence
)
from bot.db import (
    update_data_events_db,
    get_user_words_by_category_db,
    update_user_stat_learned_words_db,
    get_user_one_word_db
)
from paths import PATH_IMAGES
from bot.bot_instance import bot


@bot.on(events.NewMessage(pattern="Проверить себя 🧠"))
async def testing_words(event):
    user_id = event.message.peer_id.user_id
    step = await _get_current_user_step(user_id)

    if step in [2010, 2011, 3010, 4010, 4011, 5010]:
        return

    intro = "Выбери режим тренировки 🧠\n\n" \
            "📝 Перевод с русского на английский\n" \
            "📚 Перевод с английского на русский"
    buttons = [
        [Button.inline("📝 С русского на английский", data="test_ru_en")],
        [Button.inline("📚 С английского на русский", data="test_en_ru")]
    ]
    await event.client.send_message(event.chat_id, intro, buttons=buttons)


@bot.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.query.user_id
    data = event.data.decode("utf-8")

    if data == "test_ru_en":
        await _update_user_main_mode(user_id, "ru_en")
        await _update_user_test_words(user_id, None)
        await _update_user_test_sequence(user_id, None)
        await _update_current_user_step(user_id, 4010)
        await event.client.send_message(
            event.chat_id,
            "Если в любой момент захочешь остановиться — нажми Завершить 😊",
            buttons=await get_keyboard(["Завершить"])
        )
        await start_testing(event, user_id, mode="ru_en")

    elif data == "test_en_ru":
        await _update_user_main_mode(user_id, "en_ru")
        await _update_user_test_words(user_id, None)
        await _update_user_test_sequence(user_id, None)
        await _update_current_user_step(user_id, 2010)
        await event.client.send_message(
            event.chat_id,
            "Если в любой момент захочешь остановиться — нажми Завершить 😊",
            buttons=await get_keyboard(["Завершить"])
        )
        await start_testing(event, user_id, mode="en_ru")

    elif data == "56":
        print("56")
        step = await _get_current_user_step(user_id)
        print("step", step)
        if step in [2010, 2011, 3010, 4010, 4011, 5010]:
            print("if step in [2010, 2011, 3010, 4010, 4011, 5010]:")
            main_mode = await _get_user_main_mode(user_id)
            print("main_mode", main_mode)
            await start_testing(event, user_id, mode=main_mode)
        else:
            await event.client.send_message(
                event.chat_id,
                "Для начала выбери режим тренировки 🧠",
                buttons=[
                    [Button.inline("📝 С русского на английский", data="test_ru_en")],
                    [Button.inline("📚 С английского на русский", data="test_en_ru")]
                ]
            )
    elif data == "flip_card":
        await handle_flip_card(event, user_id)


async def start_testing(event, user_id, mode="en_ru"):
    words = await _get_user_test_sequence(user_id)
    if not words:
        category = await _get_user_choose_category(user_id=user_id)
        words_list = await get_user_words_by_category_db(user_id=user_id, category=category[0], is_system=category[1])
        words = list(words_list.keys())
        random.shuffle(words)
        await _update_user_test_sequence(user_id, words)

    current = await _get_user_test_words(user_id)

    if not current:
        current = words[0]
        await _update_user_test_words(user_id, current)

    next_word = await get_next_test_word(current, words)

    if not next_word:
        await _update_user_test_words(user_id, None)
        await _update_user_test_sequence(user_id, None)
        await _update_current_user_step(user_id, 7)

        main_mode = await _get_user_main_mode(user_id)
        opposite_mode = "ru_en" if main_mode == "en_ru" else "en_ru"
        if opposite_mode == "ru_en":
            opposite_text = "📝 Перевести с русского на английский"
            opposite_data = "test_ru_en"
        else:
            opposite_text = "📚 Перевести с английского на русский"
            opposite_data = "test_en_ru"

        await event.client.send_message(
            event.chat_id,
            f"Ура! Это было последнее слово, отличный результат! 😻\n\n"
            f"Хочешь попробовать теперь наоборот?",
            buttons=[[Button.inline(opposite_text, data=opposite_data)]]
        )
        await update_data_events_db(user_id, "testing_complete", {"step": -1})
        return

    if mode == "en_ru":
        file = f"{PATH_IMAGES}/{next_word.replace(' ', '')}_en.png"
        message = "Напиши перевод слова на русском:"
        next_step = 2011
    else:
        file = f"{PATH_IMAGES}/{next_word.replace(' ', '')}_ru.png"
        message = "Напиши перевод слова на английском:"
        next_step = 4011

    if not await check_exist_img(file):
        await create_img_card(next_word.replace(' ', '').lower(), file)

    buttons = [
        [Button.inline("🔄 Перевернуть", data="flip_card")],
        [Button.inline("Пропустить", data="56")]
    ]

    await event.client.send_message(
        event.chat_id,
        message,
        buttons=buttons,
        file=file
    )

    await _update_user_test_words(user_id, next_word)
    await _update_current_user_step(user_id, next_step)
    await update_data_events_db(user_id, "testing", {"step": next_step})


async def get_next_test_word(current, words):
    if not words:
        return None
    if not current or current not in words:
        return words[0]
    i = words.index(current)
    return words[i + 1] if i + 1 < len(words) else None


async def handle_flip_card(event, user_id):
    current_word = await _get_user_test_words(user_id)
    step = await _get_current_user_step(user_id)
    main_mode = await _get_user_main_mode(user_id)

    if step in [2010, 2011, 3010]:  # en_ru
        flip_file = f"{PATH_IMAGES}/{current_word.replace(' ', '')}_ru.png"
        next_step = 4011
    elif step in [4010, 4011, 5010]:  # ru_en
        flip_file = f"{PATH_IMAGES}/{current_word.replace(' ', '')}_en.png"
        next_step = 2011
    else:
        return

    await create_img_card(current_word.replace(' ', '').lower(), flip_file)
    # if not await check_exist_img(flip_file):
    #     await create_img_card(current_word.replace(' ', '').lower(), flip_file)

    if main_mode == "en_ru":
        message = "Переведи на русский язык:"
    elif main_mode == "ru_en":
        message = "Переведи на английский язык:"
    else:
        message = "Напиши перевод слова:"

    buttons = [
        [Button.inline("🔄 Перевернуть", data="flip_card")],
        [Button.inline("Пропустить", data="56")]
    ]

    await event.edit(
        message,
        buttons=buttons,
        file=flip_file
    )

    await _update_current_user_step(user_id, next_step)
    await update_data_events_db(user_id, "flip_card", {"step": step})


@bot.on(events.NewMessage())
async def handle_testing_answer(event):
    user_id = event.message.peer_id.user_id
    message_text = event.message.message

    if message_text in ("Проверить себя 🧠", "Завершить"):
        return

    keyboard = await get_keyboard(["Завершить"])
    step = await _get_current_user_step(user_id)

    if step in [2010, 2011, 3010, 4010, 4011, 5010]:
        category = await _get_user_choose_category(user_id=user_id)
        main_mode = await _get_user_main_mode(user_id)

        cur_test_word = await _get_user_test_words(user_id)
        user_word = await get_user_one_word_db(user_id, category[0], cur_test_word, category[1])

        if not user_word:
            await event.client.send_message(event.chat_id, "Что-то пошло не так, не найдено слово в базе.", buttons=keyboard)
            return

        user_word_en, user_word_ru_raw = user_word[0].lower(), user_word[1]
        try:
            user_word_ru = json.loads(user_word_ru_raw).lower()
        except:
            user_word_ru = user_word_ru_raw.lower()

        if main_mode == "en_ru":
            correct_answer = user_word_ru
            next_step = 2011
        elif main_mode == "ru_en":
            correct_answer = user_word_en
            next_step = 4011

        if message_text.lower() == correct_answer:
            await event.client.send_message(event.chat_id, "Иии.. верно! Так держать 🦾", buttons=keyboard)
            await update_data_events_db(user_id, "testing_success", {"step": -1, "word": message_text.lower()})
            await update_user_stat_learned_words_db(user_id, cur_test_word.lower())
            await _update_current_user_step(user_id, next_step)
            await start_testing(event, user_id, mode=main_mode)
        else:
            await event.client.send_message(
                event.chat_id,
                "Неверно 🙁 попробуй еще раз!",
                buttons=[[Button.inline("Пропустить", data="56")]]
            )
            await update_data_events_db(user_id, "testing_failed", {"step": -1, "word": message_text.lower()})
