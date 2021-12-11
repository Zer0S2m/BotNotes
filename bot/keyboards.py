from aiogram.types import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup,
    KeyboardButton, InlineKeyboardButton
)


control_notes = InlineKeyboardMarkup()

btn_create_note = InlineKeyboardButton('Создать запись', callback_data = "create_note")
btn_view_all_note = InlineKeyboardButton("Посмотреть все записи", callback_data = "view_note")

control_notes.add(btn_create_note)
control_notes.add(btn_view_all_note)


control_categories = InlineKeyboardMarkup()

btn_create_category = InlineKeyboardButton("Создать категорию", callback_data = "create_category")
btn_view_all_category = InlineKeyboardButton("Посмотреть все категории", callback_data = "view_category")

control_categories.add(btn_create_category)
control_categories.add(btn_view_all_category)


def create_btns_for_categories(categoies):
    if not categoies:
        return False

    control_choice_category = ReplyKeyboardMarkup(resize_keyboard = True, row_width = 2)
    categoies_choice = []

    for category_in in range(0, len(categoies)):
        category_title = categoies[category_in].title
        category_btn = KeyboardButton(category_title)

        categoies_choice.append(category_btn)

    control_choice_category.add(*categoies_choice)
    control_choice_category.add(
        KeyboardButton("-")
    )

    return control_choice_category
