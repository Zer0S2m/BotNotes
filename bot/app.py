from aiogram import Bot
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from sqlalchemy.orm import sessionmaker

from config import TOKEN
from config import MESSAGES

from models import User
from models import Note
from models import engine

import keyboards


bot = Bot(token = TOKEN)
dp = Dispatcher(bot)

Session = sessionmaker(bind = engine)
session = Session()


@dp.message_handler(commands = ['start'])
async def process_start_command(msg: types.Message):

	if not session.query(User).filter(User.username == msg.from_user.username).first():
		new_user = User(first_name = msg.from_user.first_name, username = msg.from_user.username)

		session.add(new_user)
		session.commit()

	await msg.reply(MESSAGES["start"])


@dp.message_handler(commands = ["help"])
async def process_help_command(msg: types.Message):
	await msg.reply(MESSAGES["help"])


@dp.callback_query_handler(lambda c: c.data == 'create_note')
async def process_callback_btn_create_note(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "create_note")


@dp.callback_query_handler(lambda c: c.data == 'view_note')
async def process_callback_btn_view_all_note(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "view_note")


@dp.message_handler(commands = ["note"])
async def echo_message(msg: types.Message):
	await bot.send_message(msg.from_user.id, f"Управление записями:", reply_markup = keyboards.control_notes)


if __name__ == '__main__':
	executor.start_polling(dp)
