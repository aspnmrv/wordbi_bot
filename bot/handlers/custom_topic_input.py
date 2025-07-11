# import ast
# import os
# from telethon import events, Button
#
# from tools import get_keyboard, build_img_cards, is_expected_steps, extract_text_from_docx
# from db_tools import (
#     _get_current_user_step,
#     _update_user_self_words,
#     _update_current_user_step,
#     _update_user_words,
#     _update_user_choose_topic
# )
# from db import (
#     get_event_from_db,
#     get_stat_use_link_db,
#     get_user_level_db,
#     update_user_words_db,
#     update_data_events_db,
#     update_user_stat_category_words_db
# )
# from globals import LIMIT_LINK_USES
# from config.config import test_user_id
# from ellie import build_cards_from_text, parse_file
# from bot_instance import bot
#
#
# @bot.on(events.NewMessage())
# async def handle_custom_topic_input(event):
#     user_id = event.message.peer_id.user_id
#     message_text = event.message.message
#
#     if not await is_expected_steps(user_id, [52]):
#         return
#
#     if message_text in ("Quiz me 📝", "Поболтать 💌", "Завершить", "Проверить себя 🧠", "Создать свой набор слов 🧬"):
#         return
#
#     if message_text.startswith("/") and await is_expected_steps(user_id, [61, 62]):
#         keyboard = await get_keyboard(["Завершить"])
#         await event.client.send_message(
#             event.chat_id,
#             "Чтобы воспользоваться командами из меню, необходимо закончить текущую генерацию карточек 🙂",
#             buttons=keyboard
#         )
#         return
#
#     last_ts_event = await get_event_from_db(user_id, "message_from_user_conv")
#
#     cnt_uses = await get_stat_use_link_db(user_id)
#
#     if cnt_uses >= LIMIT_LINK_USES and user_id != test_user_id:
#         await event.client.send_message(event.chat_id, "Слишком много запросов за сегодня 🙂")
#         await update_data_events_db(user_id, "cards_from_link_error", {"step": -1, "error": "limit"})
#         return
#
#     if not event.message.file:
#
#         await event.client.send_message(
#             event.chat_id,
#             "Формирую список слов..",
#             reply_to=event.message.id,
#             buttons=Button.clear()
#         )
#         try:
#             topics = message_text
#             level = await get_user_level_db(user_id)
#             card_words = await build_cards_from_text(topics, level, user_id)
#
#             if not card_words:
#                 keyboard = await get_keyboard(["Завершить"])
#                 await event.client.send_message(
#                     event.chat_id,
#                     "Что-то сломалось 😣\n\nУже чиним, попробуй позже",
#                     buttons=keyboard
#                 )
#             elif card_words == "None":
#                 keyboard = await get_keyboard(["Завершить"])
#                 await event.client.send_message(
#                     event.chat_id,
#                     "Кажется, выбранные темы слишком специфичны 😔\n\nПопробуй выбрать другие темы 💜",
#                     buttons=keyboard
#                 )
#                 await update_data_events_db(user_id, "cards_from_link_error", {"step": -1, "error": "specific"})
#             else:
#                 card_words = ast.literal_eval(card_words)
#                 if not isinstance(card_words, dict):
#                     keyboard = await get_keyboard(["Завершить"])
#                     await event.client.send_message(
#                         event.chat_id,
#                         "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜",
#                         buttons=keyboard
#                     )
#                 else:
#                     await _update_user_self_words(user_id, card_words)
#                     fixed_card_words = {word.replace('/', ''): translate.replace('/', '') for word, translate in card_words.items()}
#                     await build_img_cards(fixed_card_words)
#                     keyboard = await get_keyboard(["Увидеть карточки 💜"])
#                     await _update_user_words(user_id, "self", "", "en")
#                     await _update_user_choose_topic(user_id, "self")
#                     await update_user_words_db(user_id, fixed_card_words, message_text)
#                     await event.client.send_message(
#                         event.chat_id,
#                         "Чтобы увидеть карточки, жмякай на Увидеть карточки 💜",
#                         buttons=keyboard
#                     )
#                     await update_data_events_db(user_id, "cards_from_link_success", {"step": -1})
#                     await _update_current_user_step(user_id, 101)
#
#                     list_of_words = [word for word in fixed_card_words.keys()]
#                     await update_user_stat_category_words_db(user_id, list_of_words, message_text)
#         except Exception:
#             keyboard = await get_keyboard(["Завершить"])
#             await event.client.send_message(
#                 event.chat_id,
#                 "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜",
#                 buttons=keyboard
#             )
#             await update_data_events_db(user_id, "cards_from_link_error", {"step": -1, "error": "api"})
#     else:
#         file_name = event.message.file.name
#         if not file_name:
#             return
#
#         if file_name.lower().endswith(".docx"):
#             keyboard = await get_keyboard(["Завершить"])
#             await event.client.send_message(
#                 event.chat_id,
#                 "Принял файл 👍. Начинаю его обработку..",
#                 buttons=keyboard
#             )
#             try:
#                 path = await event.message.download_media()
#                 content = extract_text_from_docx(path)
#                 try:
#                     os.remove(path)
#                 except Exception as e:
#                     await update_data_events_db(user_id, "cards_from_file_remove_file_error", {"step": -1, "error": str(e)})
#
#                 if len(content.split(" ")) > 500:
#                     keyboard = await get_keyboard(["Завершить"])
#                     await event.client.send_message(
#                         event.chat_id,
#                         "Слишком много слов. Попробуй загрузить файл с количеством слов не более 20",
#                         buttons=keyboard
#                     )
#                     await update_data_events_db(
#                         user_id,
#                         "cards_from_file_many_words_error",
#                         {"step": -1, "error": "specific"}
#                     )
#                 else:
#                     if len(content) > 5:
#                         card_words = await parse_file(user_id, content)
#                         if not card_words:
#                             keyboard = await get_keyboard(["Завершить"])
#                             await event.client.send_message(
#                                 event.chat_id,
#                                 "Что-то сломалось 😣\n\nУже чиним, попробуй позже",
#                                 buttons=keyboard
#                             )
#                             await update_data_events_db(user_id, "cards_from_file_error", {"step": -1, "error": "specific"})
#                         else:
#                             card_words = ast.literal_eval(card_words)
#                             if not isinstance(card_words, dict):
#                                 keyboard = await get_keyboard(["Завершить"])
#                                 await event.client.send_message(
#                                     event.chat_id,
#                                     "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜",
#                                     buttons=keyboard
#                                 )
#                             else:
#                                 await _update_user_self_words(user_id, card_words)
#                                 fixed_card_words = {word.replace('/', ''): translate.replace('/', '') for word, translate in
#                                                     card_words.items()}
#                                 print("fixed_card_words", fixed_card_words)
#                                 await build_img_cards(fixed_card_words)
#                                 keyboard = await get_keyboard(["Увидеть карточки 💜"])
#                                 await _update_user_words(user_id, "self", "", "en")
#                                 await _update_user_choose_topic(user_id, "self")
#                                 await update_user_words_db(user_id, fixed_card_words, "my_words")
#                                 await event.client.send_message(
#                                     event.chat_id,
#                                     "Чтобы увидеть карточки, жмякай на Увидеть карточки 💜",
#                                     buttons=keyboard
#                                 )
#                                 await update_data_events_db(user_id, "cards_from_file_success", {"step": -1})
#                                 await _update_current_user_step(user_id, 391)
#
#                                 list_of_words = [word for word in fixed_card_words.keys()]
#                                 await update_user_stat_category_words_db(user_id, list_of_words, "my_words")
#             except Exception as e:
#                 print(e)
#                 keyboard = await get_keyboard(["Завершить"])
#                 await event.client.send_message(
#                     event.chat_id,
#                     "Упс..произошла какая-то ошибка. Меня уже чинят, попробуй попозже 💜",
#                     buttons=keyboard
#                 )
#                 await update_data_events_db(user_id, "cards_from_file_error_api", {"step": -1, "error": str(e)})
#         else:
#             keyboard = await get_keyboard(["Завершить"])
#             await event.client.send_message(
#                 event.chat_id,
#                 "Кажется, это не файл формата .docx 😔\n\nПопробуй еще раз 🕶",
#                 buttons=keyboard
#             )
