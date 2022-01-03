from aiogram import types
from aiogram.dispatcher import FSMContext

from config import (
	LIMIT_TITLE, LIMIT_TEXT,
	INFO_TEXT, LIMIT_CATEGORY
)

from models import (
	User, Note, Category,
	Statistics
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
			async with state.proxy() as data:
				data['category'] = False
				helpers.add_db_new_note(data = data, username = msg.from_user.username)

			await state.finish()
			await bot.send_message(msg.from_user.id, "Запись создана!")


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
			else:
				data["category"] = False

			helpers.add_db_new_note(data = data, username = msg.from_user.username)

		await state.finish()
		await bot.send_message(msg.from_user.id, "Запись создана!", reply_markup = types.ReplyKeyboardRemove())


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

				await bot.send_message(msg.from_user.id, text_note)

		await state.reset_state()


async def process_delete_note(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	helpers.delete_note(username = call.from_user.username, data = call.data, action = "delete")

	await bot.send_message(call.from_user.id, "Запись удалена!")


async def process_complete_note(call: types.CallbackQuery):
	await bot.answer_callback_query(call.id)

	helpers.delete_note(username = call.from_user.username, data = call.data, action = "complete")

	await bot.send_message(call.from_user.id, "Заметка завершена!")


async def process_note_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление записями",
		reply_markup = keyboards.control_notes
	)
