import re
import datetime as DT
from typing import List

from aiogram import types
from aiogram.types import ContentType
from aiogram.dispatcher import FSMContext

import emoji

from config import (
	DATE, FILE_EXTENSION,
	INFO_TEXT, LIMIT_CATEGORY,
	LIMIT_TITLE, LIMIT_TEXT,
	PARAMS_EDIT, MONTHS,
)

from models import Note

from state import StatesNote
from state import FSMFormNote

from dispatcher import (
	dp, bot
)

from utils.db import (
	get_user_db, get_categories_db, get_category_db,
	create_file_db, create_note_db, get_notes_db,
	get_notes_at_category, delete_note_db, edit_note_db,
	get_notes_on_date_db
)
from utils.common import (
	set_title_category, get_note_id_from_btn_note, set_choice_date_for_text,
	set_choice_date, cleans_dict_date, set_settings_file_for_note,
	parse_date_str, create_text_note, change_dict_date,
	get_dates_periods
)

import keyboards


async def process_create_note(call: types.CallbackQuery):
	await FSMFormNote.title.set()
	await bot.answer_callback_query(call.id)
	await bot.send_message(
		call.from_user.id,
		"Запишите название записи:",
		reply_markup = keyboards.create_btn_cancel("-")
	)


async def process_create_note_title_state(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()

	if len(title) > LIMIT_TITLE:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	else:
		if title == "-":
			title = False

		async with state.proxy() as data:
			data['title'] = title

		await FSMFormNote.next()
		await bot.send_message(
			msg.from_user.id,
			"Запишите описание записи:",
			reply_markup = types.ReplyKeyboardRemove()
		)


async def process_create_note_text_state(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	text = msg.text.strip()

	if len(text) > LIMIT_TEXT:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	else:
		async with state.proxy() as data:
			data['text'] = text

		user = await get_user_db(msg.from_user.username)
		categoies = await get_categories_db(user.id)

		if categoies:
			await FSMFormNote.next()
			await bot.send_message(
				msg.from_user.id,
				"Выберите категорию:",
				reply_markup = keyboards.create_btns_for_choice_categories(categoies = categoies)
			)
		else:
			await FSMFormNote.next()
			await FSMFormNote.next()
			await send_message_date_calendar(
				id = msg.from_user.id,
				is_btn_choice_date_not = True,
				text = "Выберите дату по истечению времени выполнения заметки:"
			)


async def process_create_note_category_state(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	title = set_title_category(msg.text)
	user = await get_user_db(msg.from_user.username)
	category = await get_category_db(user.id, title)

	if len(title) > LIMIT_CATEGORY:
		await msg.send_message(msg.from_user.id, f"Превышен лимит символов!\n{INFO_TEXT}")

	elif not category and title != "-":
		await bot.send_message(msg.from_user.id, "Категория с таким названием не существует!\nПерезапишите название:")

	else:
		async with state.proxy() as data:
			if title != "-":
				data["category"] = category.id

		await FSMFormNote.next()
		await send_message_date_calendar(
			id = msg.from_user.id,
			is_btn_choice_date_not = True,
			text = "Выберите дату по истечению времени выполнения заметки:"
		)


async def process_create_note_date_completion_state(call: types.CallbackQuery, state: FSMContext):
	answer_text = ""

	parse_date = parse_date_str(data = call.data)
	choice_date = False

	if parse_date["number_day"]:
		choice_date = set_choice_date(parse_date)

	current_date = DT.datetime.now()

	if re.search(r"none", call.data):
		await bot.answer_callback_query(call.id, text = "Даты не существует!")

	elif re.search(r"not", call.data):
		await bot.answer_callback_query(call.id, text = "Вы выбрали: без даты")
		await FSMFormNote.next()

		await bot.send_message(
			call.from_user.id,
			"Прикрепите файлы:\n(<b>Документ</b>, <b>фотография</b> или <b>аудио</b>)",
			reply_markup = keyboards.create_btn_cancel("-")
		)

	elif choice_date < current_date:
		await bot.answer_callback_query(call.id, text = "Прошедшая дата!")

	elif parse_date["number_day"]:
		async with state.proxy() as data:
			data["number_day"] = int(parse_date["number_day"].group(1))
			data["number_month"] = int(parse_date["number_month"].group(1))
			data["number_year"] = int(parse_date["number_year"].group(1))

		choice_date = set_choice_date_for_text(choice_date)
		answer_text = f"Вы выбрали: {choice_date}"

		cleans_dict_date()

		await bot.answer_callback_query(call.id, text = answer_text)
		await FSMFormNote.next()

		await bot.send_message(
			call.from_user.id,
			"Прикрепите файлы:\n(<b>Документ</b>, <b>фотография</b> или <b>аудио</b>)",
			reply_markup = keyboards.create_btn_cancel("-")
		)


async def process_create_note_date_completion_change_month(call: types.CallbackQuery):
	await process_view_prev_next_month_date(data = {
		"id": call.id,
		"from_user_id": call.from_user.id,
		"message_message_id": call.message.message_id,
		"data_text": call.data,
		"is_btn_choice_date_not": True,
		"text": "Выберите дату по истечению времени выполнения заметки:"
	})


async def process_view_prev_next_month_date(data: dict):
	"""
	:param data -> dict keys:
		id - callback id
		data_text - callback данные
		from_user_id - идентификатор пользователя
		message_message_id - идентификатор callback сообщения
		is_btn_choice_date_not - показывать ли кнопку (без выбора даты)
		text - выводимый текст
	"""
	await bot.answer_callback_query(data["id"])

	action = re.search(r":(\w{0,10})", data["data_text"]).group(1)

	await bot.delete_message(chat_id = data["from_user_id"], message_id = data["message_message_id"])

	if action == "prev":
		change_dict_date({
			"month": DATE["month"] - 1,
		})
	elif action == "next":
		change_dict_date({
			"month": DATE["month"] + 1,
		})

	await send_message_date_calendar(
		id = data["from_user_id"],
		is_btn_choice_date_not = data["is_btn_choice_date_not"],
		text = data["text"]
	)

async def send_message_date_calendar(
	id: int,
	is_btn_choice_date_not: bool,
	text: str
):
	await bot.send_message(
        id,
        f"{text}\n<b>-- {MONTHS[str(DATE['month'])].upper()} --</b>",
        reply_markup = keyboards.create_inline_btns_for_choice_date(is_btn_choice_date_not)
    )


async def process_create_note_file_download(msg: types.Message, state: FSMContext):
	user = await get_user_db(msg.from_user.username)

	if msg.text == None or msg.text.strip() != "-":
		data_file = await set_settings_file_for_note(msg)

		await bot.download_file(
			data_file["file_path"],
			data_file["directory"]
		)

		async with state.proxy() as data:
			new_file = await create_file_db(data = {
				"file_path": data_file["directory"],
				"file_path_id": data_file["file_id"],
				"file_extension": data_file["file_extension"],
				"user_id": user.id
			})

			data["file"] = new_file
			data["user_id"] = user.id

			await create_note_db(data = data)

	elif msg.text.strip() == "-":
		async with state.proxy() as data:
			data["user_id"] = user.id

		await create_note_db(data = data)

	await state.finish()
	await bot.send_message(
		msg.from_user.id,
		"Запись создана!",
		reply_markup = types.ReplyKeyboardRemove()
	)


async def process_view_note(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	state = dp.current_state(user = call.from_user.id)
	user = await get_user_db(call.from_user.username)
	notes = await get_notes_db(user.id)

	await state.reset_state()

	if not notes:
		await bot.send_message(call.from_user.id, "Записей нет!")

	else:
		await bot.send_message(call.from_user.id, "Записи:")
		await process_view_note_list_iteration(notes, call.from_user.id)


async def process_view_note_on_category(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	user = await get_user_db(call.from_user.username)
	categories = await get_categories_db(user.id)

	if not categories:
		await bot.send_message(call.from_user.id, "Категории отсуствуют!")
	else:
		state = dp.current_state(user = call.from_user.id)

		await state.set_state(StatesNote.all()[StatesNote.all().index("state_view_note_on_category")])
		await bot.send_message(
			call.from_user.id,
			"Выберите категорию:",
			reply_markup = keyboards.create_btns_for_choice_categories(categories)
		)


async def process_view_note_on_category_state(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)
	title = set_title_category(msg.text)
	user = await get_user_db(msg.from_user.username)
	category = await get_category_db(user.id, title)

	if category:
		notes = await get_notes_at_category(user.id, category.id)

	if title == "-":
		await bot.send_message(
			msg.from_user.id,
			emoji.emojize("Команда отменена :cross_mark:"),
			reply_markup = types.ReplyKeyboardRemove()
		)
		await state.finish()

	elif not category:
		await bot.send_message(msg.from_user.id, "Категория с таким названием не существует!\nПерезапишите название:")
	else:
		if not notes:
			await bot.send_message(
				msg.from_user.id,
				"Записей нет!",
				reply_markup = types.ReplyKeyboardRemove()
			)
		else:
			await bot.send_message(
				msg.from_user.id,
				"Записи:",
				reply_markup = types.ReplyKeyboardRemove()
			)
			await process_view_note_list_iteration(notes, msg.from_user.id)

		await state.reset_state()


async def process_view_note_on_date(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	user = await get_user_db(call.from_user.username)

	if user.notes:
		state = dp.current_state(user = call.from_user.id)

		await state.set_state(StatesNote.all()[StatesNote.all().index("state_view_note_on_date")])
		await send_message_date_calendar(
			id = call.from_user.id,
			is_btn_choice_date_not = False,
			text = "Выберите 2 периода даты:"
		)
	else:
		await bot.send_message(call.from_user.id, "Записей нет!")


async def process_view_note_on_date_state(call: types.CallbackQuery, state: FSMContext):
	state = dp.current_state(user = call.from_user.id)
	parse_date = parse_date_str(data = call.data)

	async with state.proxy() as data:
		if not "periods" in data:
			data["periods"] = {
				"first": f'{parse_date["number_year"].group(1)}-{parse_date["number_month"].group(1)}-{parse_date["number_day"].group(1)}-{0}-{0}-{0}'
			}
			await bot.answer_callback_query(
				call.id,
				text = "Первый период времени выбран! Выберите второй."
			)
		else:
			data["periods"]["second"] = \
				f'{parse_date["number_year"].group(1)}-{parse_date["number_month"].group(1)}-{parse_date["number_day"].group(1)}-{0}-{0}-{0}'
			cleans_dict_date()

			user = await get_user_db(call.from_user.username)
			dates = get_dates_periods(data)
			notes = await get_notes_on_date_db(user.id, dates)
			if notes:
				await bot.send_message(call.from_user.id, "Записи:")
				await process_view_note_list_iteration(notes, call.from_user.id)
			else:
				await bot.send_message(call.from_user.id, "Записей нет!")

			del data["periods"]
			await state.finish()
			await bot.answer_callback_query(call.id, text = "Второй период времени выбран!")


async def process_view_note_on_date_change_month(call: types.CallbackQuery):
	await process_view_prev_next_month_date(data = {
		"id": call.id,
		"from_user_id": call.from_user.id,
		"message_message_id": call.message.message_id,
		"data_text": call.data,
		"is_btn_choice_date_not": False,
		"text": "Выберите 2 периода даты:"
	})


async def process_edit_note(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	state = dp.current_state(user = call.from_user.id)

	async with state.proxy() as data:
		data["note_id"] = get_note_id_from_btn_note(call.data)

	await set_state_edit_note(call.from_user.id, state)


async def process_edit_note_state(msg: types.Message, state: FSMContext):
	text = msg.text.strip()
	text = re.sub(r"\s", "_", text).lower()
	username = msg.from_user.username

	if text == "+":
		data = await state.get_data()
		data["username"] = username

		if "param_edit" in data:
			del data["param_edit"]

		await edit_note_db(data)

		await state.finish()
		await bot.send_message(
			msg.from_user.id,
			"Редактирование завершено!",
			reply_markup = types.ReplyKeyboardRemove()
		)

	else:
		param_edit = PARAMS_EDIT[text]

		async with state.proxy() as data:
			data["param_edit"] = param_edit

		if param_edit == "category_id":
			user = await get_user_db(username)
			categories = await get_categories_db(user.id)

			if not categories:
				await bot.send_message(
					msg.from_user.id,
					"Категории отсуствуют!"
				)
				await set_state_edit_note(msg.from_user.id, state)
				return True

			else:
				reply_markup = keyboards.create_btns_for_choice_categories(categories)
				await state.set_state(StatesNote.all()[StatesNote.all().index("state_edit_note_param")])

		elif param_edit == "complete_date":
			reply_markup = keyboards.create_btn_cancel("-")

			await state.set_state(StatesNote.all()[StatesNote.all().index("state_edit_note_param_date")])
			await send_message_date_calendar(
				id = msg.from_user.id,
				is_btn_choice_date_not = True,
				text = "Выберите дату по истечению времени выполнения заметки:"
			)

		elif param_edit == "file":
			reply_markup = keyboards.create_btn_cancel("-")
			await state.set_state(StatesNote.all()[StatesNote.all().index("state_edit_note_param_file")])

		else:
			reply_markup = keyboards.create_btn_cancel("-")
			await state.set_state(StatesNote.all()[StatesNote.all().index("state_edit_note_param")])

		await bot.send_message(
			msg.from_user.id,
			"Новая запись:",
			reply_markup = reply_markup
		)


async def process_edit_note_state_param(msg: types.Message, state: FSMContext):
	text = msg.text.strip()

	async with state.proxy() as data:
		if data["param_edit"] == "category_id" and text != "-":
			user = await get_user_db(msg.from_user.username)
			category = await get_category_db(user.id, text.lower())

			if not category:
				await bot.send_message(
					msg.from_user.id,
					"Категория с таким названием не существует!"
				)
				await set_state_edit_note(msg.from_user.id, state)
				return False;

	if text != "-":
		async with state.proxy() as data:
			data[f"{data['param_edit']}"] = text

	await set_state_edit_note(msg.from_user.id, state)


async def process_edit_note_change_month(call: types.CallbackQuery, state: FSMContext):
	await process_view_prev_next_month_date(data = {
		"id": call.id,
		"from_user_id": call.from_user.id,
		"message_message_id": call.message.message_id,
		"data_text": call.data,
		"is_btn_choice_date_not": True,
		"text": "Выберите дату по истечению времени выполнения заметки:"
	})


async def process_edit_note_state_set_date(call: types.CallbackQuery, state: FSMContext):
	parse_date = parse_date_str(data = call.data)
	choice_date = False

	if parse_date["number_day"]:
		choice_date = set_choice_date(parse_date)

	current_date = DT.datetime.now()

	if re.search(r"none", call.data):
		await bot.answer_callback_query(call.id, text = "Даты не существует!")

	elif re.search(r"not", call.data):
		async with state.proxy() as data:
			data[f"{data['param_edit']}"] = "not"

		await bot.answer_callback_query(call.id, text = "Вы выбрали: без даты")
		await set_state_edit_note(call.from_user.id, state)

	elif choice_date < current_date:
		await bot.answer_callback_query(call.id, text = "Прошедшая дата!")

	elif parse_date["number_day"]:
		async with state.proxy() as data:
			data[f"{data['param_edit']}"] = {}
			data[f"{data['param_edit']}"]["number_day"] = int(parse_date["number_day"].group(1))
			data[f"{data['param_edit']}"]["number_month"] = int(parse_date["number_month"].group(1))
			data[f"{data['param_edit']}"]["number_year"] = int(parse_date["number_year"].group(1))

		choice_date = set_choice_date_for_text(choice_date)

		cleans_dict_date()

		await bot.answer_callback_query(
			call.id,
			text = f"Вы выбрали: {choice_date}"
		)

		await set_state_edit_note(call.from_user.id, state)


async def process_edit_note_state_set_file(msg: types.Message, state: FSMContext):
	if msg.text == None or msg.text.strip() != "-":
		async with state.proxy() as data:
			data[f"{data['param_edit']}"] = await set_settings_file_for_note(msg)

		await set_state_edit_note(msg.from_user.id, state)

	elif msg.text.strip() == "-":
		await set_state_edit_note(msg.from_user.id, state)


async def set_state_edit_note(user_id: int, state: FSMContext):
	await state.set_state(StatesNote.all()[StatesNote.all().index("state_edit_note")])
	await bot.send_message(
		user_id,
		"Выберите параметр для редактирования:",
		reply_markup = keyboards.create_btns_for_edit_note()
	)


async def process_delete_note(call: types.CallbackQuery):
	text = ""
	user = await get_user_db(call.from_user.username)
	note_id = get_note_id_from_btn_note(call.data)
	is_deleted_note = await delete_note_db(user.id, note_id, "delete")

	if is_deleted_note:
		text = "Этой записи уже нет!"
	else:
		await bot.send_message(call.from_user.id, emoji.emojize("Запись удалена :cross_mark:"))

	await bot.answer_callback_query(call.id, text = text)

	await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id)
	if re.search(r":file=(\w{0,5})", call.data).group(1) == "True":
		await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id - 1)


async def process_complete_note(call: types.CallbackQuery):
	text = ""
	user = await get_user_db(call.from_user.username)
	note_id = get_note_id_from_btn_note(call.data)
	is_deleted_note = await delete_note_db(user.id, note_id, "complete")

	if is_deleted_note:
		text = "Этой записи уже нет!"
	else:
		await bot.send_message(call.from_user.id, emoji.emojize("Заметка завершена :check_mark_button:"))

	await bot.answer_callback_query(call.id, text = text)
	await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id)

	if re.search(r":file=(\w{0,5})", call.data).group(1) == "True":
		await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id - 1)


async def process_view_note_list_iteration(notes: List[Note], id: int):
	for note in notes:
		data = await create_text_note(note)
		text_note = data["text"]

		if note.file_id:
			await bot.send_message(id, text_note)
			await process_view_note_file(data = {
				"id": id,
				"file_path_id": data["file_path_id"],
				"file_extension": data["file_extension"],
				"note": note
			})
		else:
			await bot.send_message(
				id,
				text_note,
				reply_markup = keyboards.create_inline_btns_for_note(note, False)
			)


async def process_view_note_file(data: dict):
	if data["file_extension"] == FILE_EXTENSION["doc"]:
		await bot.send_document(
			data["id"],
			data["file_path_id"],
			reply_markup = keyboards.create_inline_btns_for_note(data["note"], True)
		)

	elif data["file_extension"] == FILE_EXTENSION["audio"]:
		await bot.send_audio(
			data["id"],
			data["file_path_id"],
			reply_markup = keyboards.create_inline_btns_for_note(data["note"], True)
		)

	elif data["file_extension"] == FILE_EXTENSION["photo"]:
		await bot.send_photo(
			data["id"],
			data["file_path_id"],
			reply_markup = keyboards.create_inline_btns_for_note(data["note"], True)
		)


async def process_note_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление записями",
		reply_markup = keyboards.control_notes
	)


def reqister_handler_note():
	dp.register_message_handler(process_note_control, commands = ["note"])
	dp.register_message_handler(process_create_note_title_state, state = FSMFormNote.title)
	dp.register_message_handler(process_create_note_text_state, state = FSMFormNote.text)
	dp.register_message_handler(process_create_note_category_state, state = FSMFormNote.category)
	dp.register_message_handler(
		process_create_note_file_download,
		state = FSMFormNote.file_download,
		content_types = [ContentType.AUDIO, ContentType.DOCUMENT, ContentType.PHOTO, ContentType.TEXT]
	)
	dp.register_message_handler(process_view_note_on_category_state, state = StatesNote.STATE_VIEW_NOTE_ON_CATEGORY)
	dp.register_message_handler(process_edit_note_state, state = StatesNote.STATE_EDIT_NOTE)
	dp.register_message_handler(process_edit_note_state_param, state = StatesNote.STATE_EDIT_NOTE_PARAM)
	dp.register_message_handler(
		process_edit_note_state_set_file,
		state = StatesNote.STATE_EDIT_NOTE_PARAM_FILE,
		content_types = [ContentType.AUDIO, ContentType.DOCUMENT, ContentType.PHOTO, ContentType.TEXT]
	)

	dp.register_callback_query_handler(process_create_note, lambda c: c.data == 'create_note')
	dp.register_callback_query_handler(process_delete_note, text_contains = 'delete_note_')
	dp.register_callback_query_handler(process_complete_note, text_contains = 'complete_note_')
	dp.register_callback_query_handler(process_edit_note, text_contains = 'edit_note_')
	dp.register_callback_query_handler(
		process_create_note_date_completion_state,
		text_contains = 'choice_date_',
		state = FSMFormNote.date_completion
	)
	dp.register_callback_query_handler(process_view_note, lambda c: c.data == 'view_note')
	dp.register_callback_query_handler(process_view_note_on_category, lambda c: c.data == 'view_note_on_category')
	dp.register_callback_query_handler(process_view_note_on_date, lambda c: c.data == 'view_note_on_date')
	dp.register_callback_query_handler(
		process_view_note_on_date_change_month,
		text_contains = 'month_date_action',
		state = StatesNote.STATE_VIEW_NOTE_ON_DATE
	)
	dp.register_callback_query_handler(
		process_view_note_on_date_state,
		text_contains = 'choice_date_',
		state = StatesNote.STATE_VIEW_NOTE_ON_DATE
	)
	dp.register_callback_query_handler(
		process_create_note_date_completion_change_month,
		text_contains = 'month_date_action',
		state = FSMFormNote.date_completion
	)
	dp.register_callback_query_handler(
		process_edit_note_change_month,
		text_contains = "month_date_action",
		state = StatesNote.STATE_EDIT_NOTE_PARAM_DATE
	)
	dp.register_callback_query_handler(
		process_edit_note_state_set_date,
		text_contains = 'choice_date_',
		state = StatesNote.STATE_EDIT_NOTE_PARAM_DATE
	)
