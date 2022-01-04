from aiogram.types import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup,
    KeyboardButton, InlineKeyboardButton
)

import emoji

from models import Note


control_notes = InlineKeyboardMarkup(row_width = 2)

btn_create_note = InlineKeyboardButton(
    emoji.emojize('Создать :memo:'), callback_data = "create_note"
)
btn_view_all_note = InlineKeyboardButton(
    emoji.emojize("Посмотреть все записи :card_index_dividers:"), callback_data = "view_note"
)
btn_view_note_on_category = InlineKeyboardButton(
    emoji.emojize("Посмотреть записи по категории :card_file_box:"), callback_data = "view_note_on_category"
)

control_notes.add(btn_create_note)
control_notes.add(btn_view_all_note)
control_notes.add(btn_view_note_on_category)


control_categories = InlineKeyboardMarkup(row_width = 2)

btn_create_category = InlineKeyboardButton(
    emoji.emojize("Создать :memo:"), callback_data = "create_category"
)
btn_delete_category = InlineKeyboardButton(
    emoji.emojize("Удалить :wastebasket:"), callback_data = "delete_category"
)
btn_view_all_category = InlineKeyboardButton(
    emoji.emojize("Посмотреть все категории :card_file_box:"), callback_data = "view_category"
)

control_categories.row(btn_create_category, btn_delete_category)
control_categories.add(btn_view_all_category)


def create_btns_for_choice_categories(categoies: list) -> ReplyKeyboardMarkup:
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


def create_inline_btns_for_note(note: Note) -> InlineKeyboardMarkup:
    control_note = InlineKeyboardMarkup(row_width = 2)

    btn_delete_note = InlineKeyboardButton(
        emoji.emojize('Удалить :wastebasket:'), callback_data = f"delete_note_{note.id}"
    )
    btn_complete_note = InlineKeyboardButton(
        emoji.emojize('Завершить :check_mark_button:'), callback_data = f"complete_note_{note.id}"
    )
    control_note.row(btn_delete_note, btn_complete_note)

    return control_note
