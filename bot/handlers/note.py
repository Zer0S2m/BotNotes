import re
import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext

import emoji

from config import (
	LIMIT_TITLE, LIMIT_TEXT,
	INFO_TEXT, LIMIT_CATEGORY,
	MONTHS, DATE
)

from models import (
	User, Note, Category
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

	await bot.send_message(call.from_user.id, "Запишите название записи:")


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
		await bot.send_message(msg.from_user.id, "Запишите описание записи:")


async def process_create_note_text_state(msg: types.Message, state: FSMContext):
	user_id = session.query(User).filter(User.username == msg.from_user.username).first().id
	state = dp.current_state(user = msg.from_user.id)
	text = msg.text.strip()

	if len(text) > LIMIT_TEXT:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	else:
		async with state.proxy() as data:
			data['text'] = text

		if session.query(Category).first():
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

			await send_message_date_calendar(id = msg.from_user.id)


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

		await send_message_date_calendar(id = msg.from_user.id)


async def process_create_note_date_completion_state(call: types.CallbackQuery, state: FSMContext):
	answer_text = ""

	if re.search(r"day:(\d{0,2})", call.data):
		number_day = int(re.search(r"day:(\d{0,2})", call.data).group(1))
		number_month = int(re.search(r"month:(\d{0,2})", call.data).group(1))
		number_year = int(re.search(r"year:(\d{0,4})", call.data).group(1))

		async with state.proxy() as data:
			data["number_day"] = number_day
			data["number_month"] = number_month
			data["number_year"] = number_year

		choice_date = helpers.get_pub_date_note(
			date = datetime.datetime(DATE['year'], DATE['month'], DATE['day'])
		)
		choice_date = re.sub(r"\s\d{0,2}:\d{0,2}", "", choice_date)
		answer_text = f"Вы выбрали: {choice_date}"

	async with state.proxy() as data:
		helpers.add_db_new_note(data = data, username = call.from_user.username)

	helpers.cleans_dict_date()

	await bot.answer_callback_query(call.id, text = answer_text)
	await state.finish()
	await bot.send_message(call.from_user.id, "Запись создана!", reply_markup = types.ReplyKeyboardRemove())


async def process_view_prev_next_month_date(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	action = re.search(r":(\w{0,10})", call.data).group(1)

	await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id)

	if action == "prev":
		helpers.change_dict_date({
			"month": DATE["month"] - 1,
		})
	elif action == "next":
		helpers.change_dict_date({
			"month": DATE["month"] + 1,
		})

	await send_message_date_calendar(id = call.from_user.id)

async def send_message_date_calendar(id: int):
	await bot.send_message(
        id,
        f"Выберите дату по истечению времени выполнения заметки:\n<b>-- {MONTHS[str(DATE['month'])].upper()} --</b>",
        reply_markup = keyboards.create_inline_btns_for_choice_date()
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

		for note in notes:
			text_note = helpers.create_text_note(note)

			await bot.send_message(
				call.from_user.id,
				text_note,
				reply_markup = keyboards.create_inline_btns_for_note(note)
			)


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

			for note in notes:
				text_note = helpers.create_text_note(note)

				await bot.send_message(
					msg.from_user.id,
					text_note,
					reply_markup = keyboards.create_inline_btns_for_note(note)
				)

		await state.reset_state()


async def process_delete_note(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	helpers.delete_note(username = call.from_user.username, data = call.data, action = "delete")

	await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id)
	await bot.send_message(call.from_user.id, emoji.emojize("Запись удалена :cross_mark:"))


async def process_complete_note(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	helpers.delete_note(username = call.from_user.username, data = call.data, action = "complete")

	await bot.delete_message(chat_id = call.from_user.id, message_id = call.message.message_id)
	await bot.send_message(call.from_user.id, emoji.emojize("Заметка завершена :check_mark_button:"))


async def process_note_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление записями",
		reply_markup = keyboards.control_notes
	)


def reqister_handler_note():
	dp.register_message_handler(process_create_note_title_state, state = FSMFormNote.title)
	dp.register_message_handler(process_create_note_text_state, state = FSMFormNote.text)
	dp.register_message_handler(process_create_note_category_state, state = FSMFormNote.category)
	dp.register_message_handler(process_view_note_on_category_state, state = StatesNote.STATE_VIEW_NOTE_ON_CATEGORY)

	dp.register_callback_query_handler(process_create_note, lambda c: c.data == 'create_note')
	dp.register_callback_query_handler(process_delete_note, text_contains = 'delete_note_')
	dp.register_callback_query_handler(process_complete_note, text_contains = 'complete_note_')
	dp.register_callback_query_handler(
		process_create_note_date_completion_state, text_contains = 'choice_date_', state = FSMFormNote.date_completion
	)
	dp.register_callback_query_handler(process_view_note, lambda c: c.data == 'view_note')
	dp.register_callback_query_handler(process_view_note_on_category, lambda c: c.data == 'view_note_on_category')
	dp.register_callback_query_handler(
		process_view_prev_next_month_date, text_contains = 'month_date_action', state = FSMFormNote.date_completion
	)
