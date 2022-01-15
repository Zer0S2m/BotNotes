import re
import datetime as DT

from aiogram import types
from aiogram.types import ContentType
from aiogram.types import InputFile
from aiogram.dispatcher import FSMContext

from sqlalchemy import and_

import emoji

from config import (
	STATIC_FILES, FILE_EXTENSION,
	INFO_TEXT, LIMIT_CATEGORY,
	LIMIT_TITLE, LIMIT_TEXT,
	MONTHS, DATE,
)

from models import (
	User, Note, Category,
	File
)

from state import StatesNote
from state import FSMFormNote

from dispatcher import bot
from dispatcher import dp
from dispatcher import session

from handlers import helpers

import keyboards


async def process_create_note(call: types.CallbackQuery):
	await FSMFormNote.title.set()

	await bot.answer_callback_query(call.id)

	await bot.send_message(
		call.from_user.id,
		"Запишите название записи:",
		reply_markup = keyboards.create_btn_cancel_title_note()
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
	user_id = session.query(User).filter(User.username == msg.from_user.username).first().id
	state = dp.current_state(user = msg.from_user.id)
	text = msg.text.strip()

	if len(text) > LIMIT_TEXT:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	else:
		async with state.proxy() as data:
			data['text'] = text

		if session.query(Category).filter_by(
			user_id = user_id
		).first():
			await FSMFormNote.next()

			await bot.send_message(
				msg.from_user.id,
				"Выберите категорию:",
				reply_markup = keyboards.create_btns_for_choice_categories(
					categoies = session.query(Category).filter(Category.user_id == user_id).all()
				)
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
	user_id = session.query(User).filter(User.username == msg.from_user.username).first().id
	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()

	if len(title) > LIMIT_CATEGORY:
		await msg.send_message(msg.from_user.id, f"Превышен лимит символов!\n{INFO_TEXT}")

	elif not session.query(Category).filter(Category.title == title).first() and title != "-":
		await bot.send_message(msg.from_user.id, "Категория с таким названием не существует!\nПерезапишите название:")

	else:
		async with state.proxy() as data:
			if title != "-":
				data["category"] = session.query(Category).filter_by(
					title = title, user_id = user_id
				).first().id

		await FSMFormNote.next()

		await send_message_date_calendar(
			id = msg.from_user.id,
			is_btn_choice_date_not = True,
			text = "Выберите дату по истечению времени выполнения заметки:"
		)


async def process_create_note_date_completion_state(call: types.CallbackQuery, state: FSMContext):
	answer_text = ""

	parse_date = helpers.parse_date(data = call.data)
	choice_date = False

	if parse_date["number_day"]:
		choice_date = DT.datetime(
			int(parse_date["number_year"].group(1)), int(parse_date["number_month"].group(1)), int(parse_date["number_day"].group(1)), 23, 59, 59
		)

	current_date = DT.datetime.now()

	if re.search(r"none", call.data):
		await bot.answer_callback_query(call.id, text = "Даты не существует!")

	elif re.search(r"not", call.data):
		await bot.answer_callback_query(call.id, text = "Вы выбрали: без даты")
		await FSMFormNote.next()

		await bot.send_message(
			call.from_user.id,
			"Прикрепите файлы:\n(<b>Документ</b>, <b>фотография</b> или <b>аудио</b>)",
			reply_markup = keyboards.create_btn_cancel_download_file()
		)

	elif choice_date < current_date:
		await bot.answer_callback_query(call.id, text = "Прошедшая дата!")

	elif parse_date["number_day"]:
		async with state.proxy() as data:
			data["number_day"] = int(parse_date["number_day"].group(1))
			data["number_month"] = int(parse_date["number_month"].group(1))
			data["number_year"] = int(parse_date["number_year"].group(1))

		choice_date = helpers.get_pub_date_note(date = choice_date)
		choice_date = re.sub(r"\s\d{0,2}:\d{0,2}", "", choice_date)
		answer_text = f"Вы выбрали: {choice_date}"

		helpers.cleans_dict_date()

		await bot.answer_callback_query(call.id, text = answer_text)
		await FSMFormNote.next()

		await bot.send_message(
			call.from_user.id,
			"Прикрепите файлы:\n(<b>Документ</b>, <b>фотография</b> или <b>аудио</b>)",
			reply_markup = keyboards.create_btn_cancel_download_file()
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
	await bot.answer_callback_query(data["id"])

	action = re.search(r":(\w{0,10})", data["data_text"]).group(1)

	await bot.delete_message(chat_id = data["from_user_id"], message_id = data["message_message_id"])

	if action == "prev":
		helpers.change_dict_date({
			"month": DATE["month"] - 1,
		})
	elif action == "next":
		helpers.change_dict_date({
			"month": DATE["month"] + 1,
		})

	await send_message_date_calendar(
		id = data["from_user_id"],
		is_btn_choice_date_not = data["is_btn_choice_date_not"],
		text = data["text"]
	)

async def send_message_date_calendar(id: int, is_btn_choice_date_not: bool, text: str):
	await bot.send_message(
        id,
        f"{text}\n<b>-- {MONTHS[str(DATE['month'])].upper()} --</b>",
        reply_markup = keyboards.create_inline_btns_for_choice_date(is_btn_choice_date_not)
    )


async def process_create_note_file_download(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	user_id = session.query(User).filter(User.username == msg.from_user.username).first().id

	if msg.text == None or msg.text.strip() != "-":
		file_id = None
		file_extension = None

		if msg.document:
			file_id = msg.document.file_id
			file_extension = FILE_EXTENSION["doc"]

		elif msg.photo:
			file_id = msg.photo[len(msg.photo) - 1].file_id
			file_extension = FILE_EXTENSION["photo"]

		elif msg.audio:
			file_id = msg.audio.file_id
			file_extension = FILE_EXTENSION["audio"]

		file = await bot.get_file(file_id)
		file_path = file.file_path
		file_name = file_path.split("/")[-1]
		directory = f'{STATIC_FILES}/{file_path.split("/")[0]}/{file_name}'

		await bot.download_file(file_path, directory)

		async with state.proxy() as data:
			helpers.add_db_new_file(data = {
				"file_path": directory,
				"file_path_id": file_id,
				"file_extension": file_extension
			}, username = msg.from_user.username)

			data["file"] = session.query(File).filter_by(
				user_id = user_id, file_path_id = file_id
			).first().id

			helpers.add_db_new_note(data = data, username = msg.from_user.username)

	else:
		async with state.proxy() as data:
			helpers.add_db_new_note(data = data, username = msg.from_user.username)

	await state.finish()
	await bot.send_message(
		msg.from_user.id,
		"Запись создана!",
		reply_markup = types.ReplyKeyboardRemove()
	)


async def process_view_note(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	state = dp.current_state(user = call.from_user.id)
	user_id = session.query(User).filter(User.username == call.from_user.username).first().id
	notes = session.query(Note).filter(Note.user_id == user_id).all()

	await state.reset_state()

	if not notes:
		await bot.send_message(call.from_user.id, "Записей нет!")

	else:
		await bot.send_message(call.from_user.id, "Записи:")
		await process_view_note_list_iteration(notes, call.from_user.id)


async def process_view_note_on_category(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	user_id = session.query(User).filter(User.username == call.from_user.username).first().id
	categoies = session.query(Category).filter(Category.user_id == user_id).all()

	if not categoies:
		await bot.send_message(call.from_user.id, "Категории отсуствуют!")

	else:
		state = dp.current_state(user = call.from_user.id)

		await state.set_state(StatesNote.all()[StatesNote.all().index("state_view_note_on_category")])
		await bot.send_message(
			call.from_user.id,
			"Выберите категорию:",
			reply_markup = keyboards.create_btns_for_choice_categories(categoies)
		)


async def process_view_note_on_category_state(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()
	user_id = session.query(User).filter(User.username == msg.from_user.username).first().id

	if not session.query(Category).filter(Category.title == title).first():
		await bot.send_message(msg.from_user.id, "Категория с таким названием не существует!\nПерезапишите название:")

	elif title == "-":
		await bot.send_message(msg.from_user.id, "Команда отменена!", reply_markup = types.ReplyKeyboardRemove())
		await state.reset_state()

	else:
		category_id = session.query(Category).filter_by(
			title = title, user_id = user_id
		).first()

		if not category_id:
			category_id = False
		else:
			category_id = category_id.id

		notes = session.query(Note).filter_by(
			category_id = category_id, user_id = user_id
		).all()

		if not notes:
			await bot.send_message(msg.from_user.id, "Записей нет!", reply_markup = types.ReplyKeyboardRemove())

		else:
			await bot.send_message(msg.from_user.id, "Записи:", reply_markup = types.ReplyKeyboardRemove())
			await process_view_note_list_iteration(notes, msg.from_user.id)

		await state.reset_state()


async def process_view_note_on_date(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	user_id = session.query(User).filter(User.username == call.from_user.username).first().id
	note = session.query(Note).filter_by(user_id = user_id).first()

	if note:
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

	parse_date = helpers.parse_date(data = call.data)

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

			helpers.cleans_dict_date()

			user_id = session.query(User).filter(User.username == call.from_user.username).first().id
			dates = sorted([
				DT.datetime(*list(map(int, data["periods"]["first"].split("-")))),
				DT.datetime(*list(map(int, data["periods"]["second"].split("-"))))
			])

			dates[0] = dates[0] + DT.timedelta(hours = 0, minutes = 0, seconds = 0)
			dates[1] = dates[1] + DT.timedelta(hours = 23, minutes = 59, seconds = 59)

			notes = session.query(Note).filter(
				Note.user_id == user_id,
				and_(Note.pub_date >= dates[0], Note.pub_date <= dates[1])
			).all()

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


async def process_delete_note(call: types.CallbackQuery):
	text = ""
	is_deleted_note = helpers.delete_note(username = call.from_user.username, data = call.data, action = "delete")

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
	is_deleted_note = helpers.delete_note(username = call.from_user.username, data = call.data, action = "complete")

	if is_deleted_note:
		text = "Этой записи уже нет!"
	else:
		await bot.send_message(call.from_user.id, emoji.emojize("Заметка завершена :check_mark_button:"))

	await bot.answer_callback_query(call.id, text = text)

	await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id)
	if re.search(r":file=(\w{0,5})", call.data).group(1) == "True":
		await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id - 1)


async def process_view_note_list_iteration(notes: list, id: int):
	for note in notes:
		data = helpers.create_text_note(note)
		text_note = data["text"]

		if note.file:
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

	dp.register_callback_query_handler(process_create_note, lambda c: c.data == 'create_note')
	dp.register_callback_query_handler(process_delete_note, text_contains = 'delete_note_')
	dp.register_callback_query_handler(process_complete_note, text_contains = 'complete_note_')
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
