import re

from aiogram import types

from config import (
	MESSAGES, LIMIT_TITLE, LIMIT_TEXT,
	INFO_TEXT, LIMIT_CATEGORY
)

from models import (
	User, Note, Category
)

from state import StatesCreateNote

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
	state = dp.current_state(user = callback_query.from_user.id)

	await bot.answer_callback_query(callback_query.id)
	await state.set_state(StatesCreateNote.all()[StatesCreateNote.all().index("state_create_note_title")])

	await bot.send_message(callback_query.from_user.id, "Запишите название записи:")


async def process_create_note_title_state(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)
	title = msg.text.strip()

	if len(title) > LIMIT_TITLE:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	else:
		if title == "-":
			title = False

		async with state.proxy() as data:
			data['title'] = title

		await state.set_state(StatesCreateNote.all()[StatesCreateNote.all().index("state_create_note_text")])
		await bot.send_message(msg.from_user.id, "Запишите описание записи:")


async def process_create_note_text_state(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)
	text = msg.text.strip()

	if len(text) > LIMIT_TEXT:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	else:
		async with state.proxy() as data:
			data['text'] = text

		async with state.proxy() as data:
			new_note = Note(
				text = data["text"],
				user_id = session.query(User).filter(User.username == msg.from_user.username).first().id
			)

			if data["title"]:
				new_note.title = data["title"]

			session.add(new_note)
			session.commit()

		await bot.send_message(msg.from_user.id, "Запись создана!")
		await state.reset_state()


async def process_view_note(callback_query: types.CallbackQuery):
	state = dp.current_state(user = callback_query.from_user.id)
	notes = session.query(Note).filter(User.username == callback_query.from_user.username).all()

	await bot.answer_callback_query(callback_query.id)
	await state.reset_state()

	if not notes:
		await bot.send_message(callback_query.from_user.id, "Записей нет!")

	else:
		await bot.send_message(callback_query.from_user.id, "Записи:")

		for note in notes:
			pub_date = get_pub_date_note(date = session.query(Note).first().pub_date)
			text = f"Описание - {note.text}\n\n{pub_date}"

			if str(note.title)[0] != "0" and len(note.title) > 0:
				text = f"Заголовок: {note.title}\n\n{text}"

			await bot.send_message(callback_query.from_user.id, text)


async def process_create_category(callback_query: types.CallbackQuery):
	state = dp.current_state(user = callback_query.from_user.id)

	await bot.answer_callback_query(callback_query.id)
	await state.set_state(StatesCreateNote.all()[StatesCreateNote.all().index("state_create_category")])

	await bot.send_message(callback_query.from_user.id, "Запишите название категории:")


async def process_create_category_state(msg: types.Message):
	state = dp.current_state(user = msg.from_user.id)

	if len(msg.text.strip()) > LIMIT_CATEGORY:
		await msg.reply(f"Превышен лимит символов!\n{INFO_TEXT}")

	elif len(re.findall(r"^[\d\W]", msg.text.strip())) > 0:
		await msg.reply(f"Название категория не может начинаться с <b>символов</b> или с <b>цифры</b>!\n{INFO_TEXT}")

	else:
		new_category = Category(
			title = msg.text.strip(),
			user_id = session.query(User).filter(User.username == msg.from_user.username).first().id
		)

		session.add(new_category)
		session.commit()

		await msg.reply("Категория создана!")

	await state.reset_state()


async def process_note_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление записями",
		reply_markup = keyboards.control_notes
	)


def get_pub_date_note(date):
	return f'{date.strftime("%d.%m.%Y")} {date.strftime("%H:%M")}'
