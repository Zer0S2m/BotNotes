from aiogram.types import (
    ReplyKeyboardMarkup, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardButton
)


control_notes = InlineKeyboardMarkup()

btn_create_note = InlineKeyboardButton('Создать заметку', callback_data = "create_note")
btn_view_all_note = InlineKeyboardButton("Посмотреть все заметки", callback_data = "view_note")

control_notes.add(btn_create_note)
control_notes.add(btn_view_all_note)
