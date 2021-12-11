import re

from aiogram import types
from aiogram.dispatcher import FSMContext

from config import (
	MESSAGES, LIMIT_TITLE, LIMIT_TEXT,
	INFO_TEXT, LIMIT_CATEGORY
)

from models import (
	User, Note, Category
)

from state import (
	StatesNote, FSMFormCategory, FSMFormNote
)

from dispatcher import bot
from dispatcher import dp
from dispatcher import session

import keyboards


async def process_start_command(msg: types.Message):
	if not session.query(User).filter(User.username == msg.from_user.username).first():
		new_user = User(first_name = msg.from_user.first_name, username = msg.from_user.username)

		session.add(new_user)
		session.commit()

	await bot.send_message(msg.from_user.id, MESSAGES["start"])


async def process_help_command(msg: types.Message):
	await bot.send_message(msg.from_user.id, MESSAGES["help"])


async def process_info_command(msg: types.Message):
	await bot.send_message(msg.from_user.id, MESSAGES["info"])


async def process_create_note(callback_query: types.CallbackQuery):
	await FSMFormNote.title.set()

	await bot.answer_callback_query(callback_query.id)

	await bot.send_message(callback_query.from_user.id, "Запишите название записи:")


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
					categoies = session.query(Category).filter(User.username == msg.from_user.username).all()
				)
			)

		else:
			async with state.proxy() as data:
				data['category'] = False
				add_db_new_note(data = data, username = msg.from_user.username)

			await state.finish()
			await bot.send_message(msg.from_user.id, "Запись создана!")


async def process_create_note_category_state(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()

	if len(title) > LIMIT_CATEGORY:
		await msg.send_message(msg.from_user.id, f"Превышен лимит символов!\n{INFO_TEXT}")

	elif not session.query(Category).filter(Category.title == title).first() and title != "-":
		await bot.send_message(msg.from_user.id, "Категория с таким названием не существует!\nПерезапишите название:")

	else:
		async with state.proxy() as data:
			if title != "-":
				data["category"] = session.query(Category).filter(Category.title == title).first().id
			else:
				data["category"] = False

			add_db_new_note(data = data, username = msg.from_user.username)

		await state.finish()
		await bot.send_message(msg.from_user.id, "Запись создана!", reply_markup = types.ReplyKeyboardRemove())


async def process_view_note(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)

	state = dp.current_state(user = callback_query.from_user.id)
	notes = session.query(Note).filter(User.username == callback_query.from_user.username).all()

	await state.reset_state()

	if not notes:
		await bot.send_message(callback_query.from_user.id, "Записей нет!")

	else:
		await bot.send_message(callback_query.from_user.id, "Записи:")

		for note in notes:
			text_note = create_text_note(note)

			await bot.send_message(callback_query.from_user.id, text_note)


async def process_view_note_on_category(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)

	state = dp.current_state(user = callback_query.from_user.id)

	await state.set_state(StatesNote.all()[StatesNote.all().index("state_view_note_on_category")])
	await bot.send_message(
		callback_query.from_user.id,
		"Выберите категорию:",
		reply_markup = keyboards.create_btns_for_choice_categories(
			categoies = session.query(Category).filter(User.username == callback_query.from_user.username).all()
		)
	)


async def process_view_note_on_category_state(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()

	if not session.query(Category).filter(Category.title == title).first():
		await bot.send_message(msg.from_user.id, "Категория с таким названием не существует!\nПерезапишите название:")

	elif title == "-":
		await bot.send_message(msg.from_user.id, "Команда отменена!", reply_markup = types.ReplyKeyboardRemove())
		await state.reset_state()

	else:
		category_id = session.query(Category).filter(Category.title == title).first().id
		notes = session.query(Note).filter(Note.category_id == category_id).all()

		if not notes:
			await bot.send_message(msg.from_user.id, "Записей нет!")

		else:
			await bot.send_message(msg.from_user.id, "Записи:", reply_markup = types.ReplyKeyboardRemove())

			for note in notes:
				text_note = create_text_note(note)

				await bot.send_message(msg.from_user.id, text_note)

		await state.reset_state()


async def process_note_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление записями",
		reply_markup = keyboards.control_notes
	)


async def process_create_category(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)

	await FSMFormCategory.title.set()

	await bot.send_message(callback_query.from_user.id, "Запишите название категории:")


async def process_create_category_state(msg: types.Message, state: FSMContext):
	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()

	if len(title) > LIMIT_CATEGORY:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	elif len(re.findall(r"^[\d\W]", title)) > 0:
		await msg.reply(
			f"Название категория не может начинаться с <b>символов</b> или с <b>цифры</b>!\nПерезапишите название!\n{INFO_TEXT}"
		)

	elif session.query(Category).filter(Category.title == title).first():
		await msg.reply("Категория с таким названием уже существует!\nПерезапишите название:")

	else:
		new_category = Category(
			title = msg.text.strip(),
			user_id = session.query(User).filter(User.username == msg.from_user.username).first().id
		)

		session.add(new_category)
		session.commit()

		await state.finish()
		await msg.reply("Категория создана!")


async def process_view_category(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)

	categories = session.query(Category).filter(User.username == callback_query.from_user.username).all()

	if not categories:
		await bot.send_message(callback_query.from_user.id, "Категории отсуствуют!")

	else:
		text = "Категории:\n"

		for category_in in range(0, len(categories)):
			notes_at_category = len(session.query(Note).filter(Note.category_id == categories[category_in].id).all())
			text += f"\n{category_in + 1}) {categories[category_in].title} ({notes_at_category})"

		await bot.send_message(callback_query.from_user.id, text)


async def process_category_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление категориями",
		reply_markup = keyboards.control_categories
	)


def add_db_new_note(data, username):
	new_note = Note(
		text = data["text"],
		user_id = session.query(User).filter(User.username == username).first().id
	)

	if data["title"]:
		new_note.title = data["title"]

	if data["category"]:
		new_note.category_id = data["category"]

	session.add(new_note)
	session.commit()


def create_text_note(note):
	pub_date = get_pub_date_note(date = session.query(Note).first().pub_date)
	text = f"<b>Описание</b> - {note.text}"

	if str(note.title)[0] != "0" and len(note.title) > 0:
		text = f"<b>Заголовок</b> - {note.title}\n\n{text}"

	if note.category_id:
		text += f"\n\n<b>Категория</b> - {session.query(Category).filter(Category.id == note.category_id).first().title}"

	text += f"\n\n{pub_date}"

	return text


def get_pub_date_note(date):
	return f'{date.strftime("%d.%m.%Y")} {date.strftime("%H:%M")}'
