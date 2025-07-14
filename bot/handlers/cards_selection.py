from telethon import events, Button
from bot.db_tools import _update_current_user_step
from bot.db import get_user_categories_db, delete_category_for_user
from bot.tools import get_keyboard
from bot.bot_instance import bot

user_selected_delete = {}


@bot.on(events.CallbackQuery(pattern=r"^(delete_categories|mark:|bulk_delete|end)"))
async def handle_cards_selection(event):
    user_id = event.original_update.user_id
    data_filter = event.data.decode("utf-8")

    if data_filter == "delete_categories":
        categories = await get_user_categories_db(user_id)
        if categories:
            await _update_current_user_step(user_id, 904)
            user_selected_delete[user_id] = set()

            selected = user_selected_delete.get(user_id, set())
            buttons = []
            for cat in categories:
                mark = "✅" if cat in selected else "❌"
                buttons.append([Button.inline(f"{mark} {cat}", data=f"mark:{cat}")])
            buttons.append([Button.inline("Удалить выбранные 🗑", data="bulk_delete")])
            buttons.append([Button.inline("Назад", data="end")])

            await event.client.send_message(
                event.chat_id,
                "Выбери подборки для удаления. Галочки показывают твой выбор 👇",
                buttons=buttons
            )
        else:
            keyboard = await get_keyboard(["Назад"])
            await event.client.send_message(
                event.chat_id,
                "У тебя пока нет подборок для удаления 😔",
                buttons=keyboard
            )

    elif data_filter.startswith("mark:"):
        category = data_filter.split(":", 1)[1]
        selected = user_selected_delete.get(user_id, set())
        if category in selected:
            selected.remove(category)
        else:
            selected.add(category)
        user_selected_delete[user_id] = selected

        categories = await get_user_categories_db(user_id)
        await send_delete_menu(event, user_id, categories)

    elif data_filter == "bulk_delete":
        selected = user_selected_delete.get(user_id, set())
        if selected:
            for category in selected:
                await delete_category_for_user(user_id, category)
            await event.client.send_message(
                event.chat_id,
                f"Удалены подборки: {', '.join(selected)} 🗑"
            )
        else:
            await event.client.send_message(
                event.chat_id,
                "Ты не выбрал ни одной подборки для удаления 🤷"
            )

        categories = await get_user_categories_db(user_id)
        if categories:
            user_selected_delete[user_id] = set()
            await send_delete_menu(event, user_id, categories)
        else:
            keyboard = await get_keyboard(["Назад"])
            await event.client.send_message(
                event.chat_id,
                "Все подборки удалены 🥳",
                buttons=keyboard
            )

    elif data_filter == "end":
        categories = await get_user_categories_db(user_id)
        if categories:
            await _update_current_user_step(user_id, 902)
            buttons = [[Button.inline(cat, data=f"cat:{cat}")] for cat in categories]
            buttons.append([Button.inline("Удалить подборки 🗑", data="delete_categories")])
            buttons.append([Button.inline("Назад", data="back_to_type")])
            await event.client.send_message(
                event.chat_id,
                "Окей, вернемся к твоим подборкам 📚\n\nТеперь можно выбрать нужную подборку",
                buttons=buttons
            )
        else:
            keyboard = await get_keyboard(["Создать свой набор слов 🧬", "Назад"])
            await event.client.send_message(
                event.chat_id,
                "У тебя пока нет подборок 😔",
                buttons=keyboard
            )


async def send_delete_menu(event, user_id, categories):
    selected = user_selected_delete.get(user_id, set())
    buttons = []
    for cat in categories:
        mark = "✅" if cat in selected else "❌"
        buttons.append([Button.inline(f"{mark} {cat}", data=f"mark:{cat}")])
    buttons.append([Button.inline("Удалить выбранные 🗑", data="bulk_delete")])
    buttons.append([Button.inline("Назад", data="end")])

    await event.edit(
        "Выбери подборки для удаления. Галочки показывают твой выбор 👇",
        buttons=buttons
    )
