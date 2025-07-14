from telethon import events, Button
from bot.db_tools import (
    _get_current_user_step,
    _update_current_user_step,
    _update_user_choose_category,
    _get_user_choose_category,
    _update_user_self_words
)
from bot.db import (
    get_user_words_db,
    get_user_categories_db,
    get_user_words_by_category_db,
    update_data_events_db
)
from bot.tools import get_keyboard, build_img_cards, is_expected_steps, is_valid_base_date, normalize_filename
from bot.handlers.cards_by_interest import get_start_cards
from bot.bot_instance import bot


async def show_categories_menu(event, user_id, is_system_words=False):
    categories = await get_user_categories_db(user_id, is_system=is_system_words)

    if categories:
        await _update_current_user_step(user_id, 902)
        if is_system_words:
            buttons = [[Button.inline(cat, data=f"base_cat:{cat}")] for cat in categories]
            buttons.append([Button.inline("Удалить подборки 🗑", data="delete_categories")])
        else:
            buttons = [[Button.inline(cat, data=f"cat:{cat}")] for cat in categories]
            buttons.append([Button.inline("Удалить подборки 🗑", data="delete_categories")])
        await event.client.send_message(
            event.chat_id,
            "Выбери подборку карточек 📚",
            buttons=buttons
        )
    else:
        keyboard = await get_keyboard(["Создать свой набор слов 🧬", "Назад"])
        await event.client.send_message(
            event.chat_id,
            "У тебя пока нет подборок 😔",
            buttons=keyboard
        )
        await update_data_events_db(user_id, "my_cards", {"step": -1, "error": "without cards"})


@bot.on(events.CallbackQuery(pattern=r"^(10|11|cat:|back_to_type|base_cat)"))
async def handle_get_cards_callback(event):
    user_id = event.original_update.user_id
    step = await _get_current_user_step(user_id)
    if not await is_expected_steps(user_id, [545, 902, 51]):
        return

    data_filter = event.data.decode("utf-8")

    if data_filter == "10":
        await show_categories_menu(event, user_id, is_system_words=True)

    elif data_filter == "11":
        await show_categories_menu(event, user_id)

    elif data_filter.startswith("cat:"):
        category = data_filter.split(":", 1)[1]
        words_dict = await get_user_words_by_category_db(user_id, category, is_system=False)
        if words_dict:
            await _update_current_user_step(user_id, 903)
            await build_img_cards(words_dict, user_id, normalize_filename(category))
            await _update_user_choose_category(user_id=user_id, data=category, is_system=False)
            await _update_user_self_words(user_id, words_dict)
            text = f"📚 Вот слова из подборки '{category}':\n\n"
            for word, translation in words_dict.items():
                text += f"▪️ {word} — {translation}\n"
            keyboard = await get_keyboard(["Проверить себя 🧠", "Назад"])
            await event.client.send_message(
                event.chat_id,
                text,
                buttons=keyboard
            )
        else:
            keyboard = await get_keyboard(["Назад"])
            await event.client.send_message(
                event.chat_id,
                "Кажется, в этой подборке пока нет слов 😔",
                buttons=keyboard
            )
    elif data_filter.startswith("base_cat:"):
        category = data_filter.split(":", 1)[1]
        words_dict = await get_user_words_by_category_db(user_id, category, is_system=True)
        if words_dict:
            await _update_current_user_step(user_id, 907)
            await build_img_cards(words_dict, user_id, normalize_filename(category))
            await _update_user_choose_category(user_id=user_id, data=category, is_system=True)
            await _update_user_self_words(user_id, words_dict)
            text = f"📚 Вот слова из подборки '{category}':\n\n"
            for word, translation in words_dict.items():
                text += f"▪️ {word} — {translation}\n"
            keyboard = await get_keyboard(["Проверить себя 🧠", "Назад"])
            await event.client.send_message(
                event.chat_id,
                text,
                buttons=keyboard
            )
        else:
            keyboard = await get_keyboard(["Назад"])
            await event.client.send_message(
                event.chat_id,
                "Кажется, в этой подборке пока нет слов 😔",
                buttons=keyboard
            )

    elif data_filter == "back_to_type":
        await _update_current_user_step(user_id, 545)
        text = (
            "Выбери тип карточек, которые нужно открыть🤗\n\n"
            "▪️ По интересам – карточки, созданные на основе твоих интересов\n"
            "▪️ Мои карточки – карточки, созданные из своего набора слов или из файла"
        )

        buttons = [
            [Button.inline("По интересам", data="10"), Button.inline("Мои карточки", data="11")]
        ]

        await event.edit(
            text,
            buttons=buttons
        )

    await update_data_events_db(user_id, "get_cards", {"step": step})
