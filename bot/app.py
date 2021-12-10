import re

from aiogram import Bot
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from sqlalchemy.orm import sessionmaker

from config import (
	TOKEN, MESSAGES,
	LIMIT_TITLE, LIMIT_TEXT
)

from models import User
from models import Note
from models import engine

from state import StatesCreateNote

import keyboards


bot = Bot(token = TOKEN)
dp = Dispatcher(bot, storage = MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

Session = sessionmaker(bind = engine)
session = Session()


@dp.message_handler(commands = ['start'])
async def process_start_command(msg: types.Message):
	if not session.query(User).filter(User.username == msg.from_user.username).first():
		new_user = User(first_name = msg.from_user.first_name, username = msg.from_user.username)

		session.add(new_user)
		session.commit()

	await bot.send_message(msg.from_user.id, MESSAGES["start"])


@dp.message_handler(commands = ["help"])
async def process_help_command(msg: types.Message):
	await bot.send_message(msg.from_user.id, MESSAGES["help"])


@dp.message_handler(commands = ["info"])
async def process_help_command(msg: types.Message):
	await bot.send_message(msg.from_user.id, MESSAGES["info"])


@dp.callback_query_handler(lambda c: c.data == 'create_note')
async def process_callback_btn_create_note(callback_query: types.CallbackQuery):
	state = dp.current_state(user = callback_query.from_user.id)

	await bot.answer_callback_query(callback_query.id)
	await state.set_state(StatesCreateNote.all()[1])
	await bot.send_message(callback_query.from_user.id, "Запишите заметку:")


@dp.callback_query_handler(lambda c: c.data == 'view_note')
async def process_callback_btn_view_all_note(callback_query: types.CallbackQuery):
	state = dp.current_state(user = callback_query.from_user.id)
	notes = session.query(Note).filter(User.username == callback_query.from_user.username).all()

	await bot.answer_callback_query(callback_query.id)
	await state.reset_state()

	if not notes:
		await bot.send_message(callback_query.from_user.id, "Записей нет!")

	else:
		await bot.send_message(callback_query.from_user.id, "Записи:")

		for note in notes:
			await bot.send_message(
				callback_query.from_user.id,
				f"Заголовок - {note.title}\n\nОписание - {note.text}"
			)


@dp.message_handler(commands = ["note"])
async def echo_message(msg: types.Message):
	await bot.send_message(
		msg.from_user.id,
		f"Управление записями\nДля получения информации воспользуйтесь командой: /info",
		reply_markup = keyboards.control_notes
	)


@dp.message_handler(state = StatesCreateNote.TEST_STATE_1)
async def first_test_state_case_met(msg: types.Message):
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
			title = msg.text,
			text = msg.text,
			user_id = session.query(User).filter(User.username == msg.from_user.username).first().id
		)

		session.add(new_note)
		session.commit()

		await state.reset_state()
		await msg.reply("Запись создана!")


if __name__ == '__main__':
	executor.start_polling(dp)
