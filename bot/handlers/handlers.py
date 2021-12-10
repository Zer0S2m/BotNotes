import re

from aiogram import types

from config import (
	MESSAGES, LIMIT_TITLE, LIMIT_TEXT
)

from models import User
from models import Note

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
	await state.set_state(StatesCreateNote.all()[1])
	await bot.send_message(callback_query.from_user.id, "Запишите заметку:")


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
			pub_date = get_pub_date_note(
				date = session.query(Note).first().pub_date
			)

			await bot.send_message(
				callback_query.from_user.id,
				f"Заголовок - {note.title}\n\nОписание - {note.text}\n\n{pub_date}"
			)


async def process_note_control(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление записями\nДля получения информации воспользуйтесь командой: /info",
		reply_markup = keyboards.control_notes
	)


async def process_create_note_state(msg: types.Message):
	title = re.findall(r"title:\s([\s\w\S]{0,1000})\ntext", msg.text)[0].strip()
	text = re.findall(r"text:\s([\s\w\S]{0,1000})", msg.text)[0].strip()

	if len(title) > LIMIT_TITLE or len(text) > LIMIT_TEXT:
		await msg.reply(
			"Превышен лимит символов!\nДля более получении подробной информации воспользуйтесь командой: /info"
		)

	if not text:
		await msg.reply(
			"Описание записки обязательно\nДля более получении подробной информации воспользуйтесь командой: /info"
		)

	else:
		state = dp.current_state(user = msg.from_user.id)

		new_note = Note(
			title = title,
			text = text,
			user_id = session.query(User).filter(User.username == msg.from_user.username).first().id
		)

		session.add(new_note)
		session.commit()

		await state.reset_state()
		await msg.reply("Запись создана!")


def get_pub_date_note(date):
	return f'{date.strftime("%d.%m.%Y")} {date.strftime("%H:%M")}'
