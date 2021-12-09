from aiogram import Bot
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from sqlalchemy.orm import sessionmaker

from config import TOKEN

from models import User
from models import engine

import keyboards


bot = Bot(token = TOKEN)
dp = Dispatcher(bot)

Session = sessionmaker(bind = engine)
session = Session()


@dp.message_handler(commands = ['start'])
async def process_start_command(message: types.Message):

	if not session.query(User).filter(User.username == message.from_user.username).first():
		new_user = User(first_name = message.from_user.first_name, username = message.from_user.username)

		session.add(new_user)
		session.commit()

	await message.reply("Привет!\nНапиши мне что-нибудь!")


@dp.message_handler(commands = ['hello'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!", reply_markup = keyboards.greet_kb)


@dp.message_handler(commands = ['help'])
async def process_help_command(message: types.Message):
	await message.reply("Напиши мне что-нибудь, и я отпрпавлю этот текст тебе в ответ!")


@dp.message_handler()
async def echo_message(msg: types.Message):
	await bot.send_message(msg.from_user.id, msg.text)


if __name__ == '__main__':
	executor.start_polling(dp)
