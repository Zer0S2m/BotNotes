import datetime as DT

from aiogram.types import (
	ReplyKeyboardMarkup, InlineKeyboardMarkup,
	KeyboardButton, InlineKeyboardButton
)

import emoji

from models import Note

from config import DATE


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
btn_view_note_on_date = InlineKeyboardButton(
	emoji.emojize("Посмотреть записи по дате :four_o’clock:"), callback_data = "view_note_on_date"
)

control_notes.add(btn_create_note)
control_notes.add(btn_view_all_note)
control_notes.add(btn_view_note_on_category)
control_notes.add(btn_view_note_on_date)


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


def create_inline_btns_for_note(note: Note, is_file: bool) -> InlineKeyboardMarkup:
	control_note = InlineKeyboardMarkup(row_width = 2)

	btn_delete_note = InlineKeyboardButton(
		emoji.emojize('Удалить :wastebasket:'), callback_data = f"delete_note_{note.id}:file={is_file}"
	)
	btn_complete_note = InlineKeyboardButton(
		emoji.emojize('Завершить :check_mark_button:'), callback_data = f"complete_note_{note.id}:file={is_file}"
	)
	control_note.row(btn_delete_note, btn_complete_note)

	return control_note


def create_inline_btns_for_choice_date(is_btn_choice_date_not: bool) -> InlineKeyboardMarkup:
	control_note_date = InlineKeyboardMarkup(row_width = 7)

	btn_prev_month_date = InlineKeyboardButton(
		emoji.emojize(":left_arrow: Прошлый"), callback_data = "month_date_action:prev"
	)
	btn_next_month_date = InlineKeyboardButton(
		emoji.emojize("Следующий :right_arrow:"), callback_data = "month_date_action:next"
	)
	btn_not_date = InlineKeyboardButton(
		emoji.emojize("Без выбора даты :calendar:"), callback_data = "choice_date_not"
	)

	date_choice = []

	days_current_month = last_day_of_month(DT.date(DATE["year"], DATE["month"], 1)).day
	first_day_month = DT.date(DATE["year"], DATE["month"], 1).weekday()
	last_day_month = DT.date(DATE["year"], DATE["month"], days_current_month).weekday()

	if first_day_month != 0:
		for day in range(0, first_day_month):
			date_btn = InlineKeyboardButton("-", callback_data = "choice_date_none")
			date_choice.append(date_btn)

	for day in range(0, days_current_month):
		# В "callback_data" передаётся номер дня, номер месяца и номер года
		date_btn = InlineKeyboardButton(
			f"{day + 1}",
			callback_data = f"choice_date_day:{day + 1}|month:{DATE['month']}|year:{DATE['year']}"
		)
		date_choice.append(date_btn)

	for day in range(last_day_month, 6):
		date_btn = InlineKeyboardButton("-", callback_data = "choice_date_none")
		date_choice.append(date_btn)

	control_note_date.add(*date_choice)
	control_note_date.row(btn_prev_month_date, btn_next_month_date)

	if is_btn_choice_date_not:
		control_note_date.add(btn_not_date)

	return control_note_date


def last_day_of_month(any_day):
	next_month = any_day.replace(day = 28) + DT.timedelta(days = 4)
	return next_month - DT.timedelta(days = next_month.day)


def create_btn_cancel_download_file() -> ReplyKeyboardMarkup:
	control_download_file = ReplyKeyboardMarkup(resize_keyboard = True)

	control_download_file.add(
		KeyboardButton("-")
	)

	return control_download_file


def create_btn_cancel_title_note() -> ReplyKeyboardMarkup:
	control_note_create_title = ReplyKeyboardMarkup(resize_keyboard = True)

	control_note_create_title.add(
		KeyboardButton("-")
	)

	return control_note_create_title
