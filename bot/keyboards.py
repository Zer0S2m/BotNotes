from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup


btn_create_note = InlineKeyboardButton('Создать заметку', callback_data = "create_note")
btn_view_all_note = InlineKeyboardButton("Посмотреть все заметки", callback_data = "view_note")

control_notes = InlineKeyboardMarkup(row_width = 2).row(
    btn_create_note, btn_view_all_note
)
